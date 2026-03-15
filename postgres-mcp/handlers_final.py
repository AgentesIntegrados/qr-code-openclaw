"""PostgreSQL handlers - following docker-mcp pattern"""
import os
import psycopg
from typing import List, Dict, Any, Tuple, Callable, Awaitable
import mcp.types as types

# Definição do tipo para os handlers para clareza
HandlerFunction = Callable[[dict, str], Awaitable[dict]]

class PostgresHandlers:
    """Handler class for PostgreSQL operations."""
    
    @staticmethod
    def get_connection_string(db_url: str = None) -> str:
        """Get database connection string from parameter or environment."""
        if db_url:
            return db_url
        return os.environ.get("DATABASE_URI", "")
    
    @staticmethod
    async def handle_test_connection(arguments: Dict[str, Any] | None) -> List[types.TextContent]:
        """Test database connection."""
        try:
            db_url = PostgresHandlers.get_connection_string(
                arguments.get("database_url") if arguments else None
            )
            
            if not db_url:
                return [types.TextContent(
                    type="text",
                    text="Error: No database URL provided. Set DATABASE_URI environment variable or provide database_url parameter."
                )]
            
            # Try to connect
            try:
                conn = psycopg.connect(db_url)
                conn.close()
                return [types.TextContent(
                    type="text",
                    text=f"✓ Successfully connected to PostgreSQL\nDatabase URL: {db_url[:30]}..."
                )]
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=f"✗ Connection failed: {str(e)}"
                )]
                
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
    
    @staticmethod
    async def handle_list_schemas(arguments: Dict[str, Any] | None) -> List[types.TextContent]:
        """List all schemas in the database."""
        try:
            db_url = PostgresHandlers.get_connection_string()
            
            if not db_url:
                return [types.TextContent(
                    type="text",
                    text="Error: No database URL configured. Set DATABASE_URI environment variable."
                )]
            
            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            schema_name,
                            schema_owner,
                            CASE
                                WHEN schema_name LIKE 'pg_%' THEN 'System Schema'
                                WHEN schema_name = 'information_schema' THEN 'System Information Schema'
                                ELSE 'User Schema'
                            END as schema_type
                        FROM information_schema.schemata
                        ORDER BY schema_type, schema_name
                    """)
                    
                    rows = cur.fetchall()
                    
                    if not rows:
                        return [types.TextContent(type="text", text="No schemas found.")]
                    
                    result = "Available schemas:\n\n"
                    current_type = None
                    
                    for schema_name, owner, schema_type in rows:
                        if schema_type != current_type:
                            current_type = schema_type
                            result += f"\n{schema_type}:\n"
                        result += f"  - {schema_name} (owner: {owner})\n"
                    
                    return [types.TextContent(type="text", text=result)]
                    
        except psycopg.OperationalError as e:
            return [types.TextContent(
                type="text",
                text=f"Database connection error: {str(e)}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
    
    @staticmethod
    async def handle_list_tables(arguments: Dict[str, Any] | None) -> List[types.TextContent]:
        """List all tables in a schema."""
        try:
            db_url = PostgresHandlers.get_connection_string()
            schema_name = arguments.get("schema", "public") if arguments else "public"
            
            if not db_url:
                return [types.TextContent(
                    type="text",
                    text="Error: No database URL configured. Set DATABASE_URI environment variable."
                )]
            
            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            tablename as table_name,
                            pg_size_pretty(pg_total_relation_size(quote_ident(schemaname)||'.'||quote_ident(tablename))) as size,
                            (SELECT COUNT(*) FROM information_schema.columns 
                             WHERE table_schema = t.schemaname AND table_name = t.tablename) as columns
                        FROM pg_tables t
                        WHERE schemaname = %s
                        ORDER BY tablename
                    """, (schema_name,))
                    
                    rows = cur.fetchall()
                    
                    if not rows:
                        return [types.TextContent(
                            type="text", 
                            text=f"No tables found in schema '{schema_name}'."
                        )]
                    
                    result = f"Tables in schema '{schema_name}':\n\n"
                    for table_name, size, columns in rows:
                        result += f"  - {table_name} ({columns} columns, {size})\n"
                    
                    return [types.TextContent(type="text", text=result)]
                    
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
    
    @staticmethod
    async def handle_execute_query(arguments: Dict[str, Any] | None) -> List[types.TextContent]:
        """Execute a SQL query."""
        try:
            if not arguments or "query" not in arguments:
                return [types.TextContent(
                    type="text",
                    text="Error: Query parameter is required."
                )]
            
            db_url = PostgresHandlers.get_connection_string()
            query = arguments["query"]
            
            if not db_url:
                return [types.TextContent(
                    type="text",
                    text="Error: No database URL configured. Set DATABASE_URI environment variable."
                )]
            
            # Medida de segurança básica: impedir DML/DDL
            restricted_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]
            # Permitir EXPLAIN, mesmo que contenha palavras-chave restritas (ex: EXPLAIN ANALYZE UPDATE...)
            # E também permitir comandos que começam com "SET" para configuração de sessão.
            if not query.upper().strip().startswith("EXPLAIN") and \
               not query.upper().strip().startswith("SET") and \
               any(keyword in query.upper() for keyword in restricted_keywords):
                return [types.TextContent(
                    type="text",
                    text="Error: Apenas queries SELECT, EXPLAIN e SET são permitidas."
                )]
            
            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    
                    # Get column names
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    
                    # Get rows
                    rows = cur.fetchall()
                    
                    if not rows:
                        return [types.TextContent(type="text", text="Query executed successfully. No results returned.")]
                    
                    # Format results
                    result = f"Query results ({len(rows)} rows):\n\n"
                    
                    # Add column headers
                    result += " | ".join(columns) + "\n"
                    result += "-" * (len(" | ".join(columns))) + "\n"
                    
                    # Add rows (limit to first 50 for readability)
                    for i, row in enumerate(rows[:50]):
                        result += " | ".join(str(val) for val in row) + "\n"
                    
                    if len(rows) > 50:
                        result += f"\n... and {len(rows) - 50} more rows"
                    
                    return [types.TextContent(type="text", text=result)]
                    
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error executing query: {str(e)}"
            )]

    @staticmethod
    async def handle_explain_query(arguments: Dict[str, Any] | None) -> List[types.TextContent]:
        """
        Execute EXPLAIN on the provided query and return the execution plan with analysis.
        """
        try:
            if not arguments or "query" not in arguments:
                return [types.TextContent(
                    type="text",
                    text="Error: Query parameter is required."
                )]
            
            db_url = PostgresHandlers.get_connection_string()
            query = arguments["query"]
            analyze = arguments.get("analyze", False)
            buffers = arguments.get("buffers", False)
            format_type = arguments.get("format", "TEXT").upper()
            
            if not db_url:
                return [types.TextContent(
                    type="text",
                    text="Error: No database URL configured. Set DATABASE_URI environment variable."
                )]
            
            # Build EXPLAIN options
            options = []
            options.append(f"FORMAT {format_type}")
            if analyze:
                options.append("ANALYZE true")
            if buffers and analyze:  # BUFFERS requires ANALYZE
                options.append("BUFFERS true")
            
            # Construct EXPLAIN query
            explain_query = f"EXPLAIN ({', '.join(options)}) {query}"
            
            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(explain_query)
                    rows = cur.fetchall()
                    
                    if not rows:
                        return [types.TextContent(type="text", text="No execution plan returned.")]
                    
                    # Format the output
                    result = "Query Execution Plan:\n" + "=" * 50 + "\n\n"
                    
                    if format_type == "TEXT":
                        # Parse and format text output
                        plan_lines = []
                        for row in rows:
                            plan_lines.append(row[0])
                        
                        result += "\n".join(plan_lines)
                        
                        # Add analysis and suggestions
                        result += "\n\n" + "=" * 50 + "\n"
                        result += "Performance Analysis:\n\n"
                        
                        # Check for common performance issues
                        plan_text = "\n".join(plan_lines)
                        suggestions = []
                        
                        # Sequential scan detection
                        import re
                        if "Seq Scan" in plan_text:
                            seq_scans = re.findall(r'Seq Scan on (\w+)', plan_text)
                            for table in set(seq_scans):
                                # Try to find cost info
                                cost_match = re.search(rf'Seq Scan on {table}.*cost=[\d.]+\.\.(\d+\.\d+)', plan_text)
                                if cost_match and float(cost_match.group(1)) > 1000:
                                    suggestions.append(f"⚠️  High-cost sequential scan on '{table}'. Consider adding an index.")
                                else:
                                    suggestions.append(f"📌 Sequential scan on '{table}'. May need an index if table is large.")
                        
                        # Nested loop warning
                        if "Nested Loop" in plan_text:
                            if analyze:
                                # Look for actual rows in nested loops
                                nested_matches = re.findall(r'Nested Loop.*actual time=[\d.]+\.\.[\d.]+.*rows=(\d+)', plan_text)
                                if nested_matches and any(int(r) > 10000 for r in nested_matches):
                                    suggestions.append("⚠️  Nested loop with high row count. Consider hash or merge join.")
                            else:
                                suggestions.append("📌 Nested loop detected. Run with analyze=True for performance metrics.")
                        
                        # Check execution time (if ANALYZE was used)
                        if analyze:
                            total_time_match = re.search(r'Planning Time:\s*([\d.]+)\s*ms.*Execution Time:\s*([\d.]+)\s*ms', plan_text, re.DOTALL)
                            if total_time_match:
                                planning = float(total_time_match.group(1))
                                execution = float(total_time_match.group(2))
                                total = planning + execution
                                
                                result += f"\n📊 Timing Summary:\n"
                                result += f"   - Planning Time: {planning:.2f} ms\n"
                                result += f"   - Execution Time: {execution:.2f} ms\n"
                                result += f"   - Total Time: {total:.2f} ms\n\n"
                                
                                if execution > 1000:
                                    suggestions.append(f"⚠️  Slow query execution: {execution:.1f}ms. Optimization needed.")
                                if planning > 100:
                                    suggestions.append(f"📌 High planning time: {planning:.1f}ms. Complex query structure.")
                        
                        # External operations
                        if "external" in plan_text.lower():
                            suggestions.append("⚠️  External disk operations detected. Consider increasing work_mem.")
                        
                        # Hash operations
                        if "Hash" in plan_text:
                            hash_batches = re.findall(r'Batches:\s*(\d+)', plan_text)
                            if hash_batches and any(int(b) > 1 for b in hash_batches):
                                suggestions.append("⚠️  Hash join spilling to disk. Increase work_mem for better performance.")
                        
                        # Index usage
                        if "Index Scan" in plan_text:
                            suggestions.append("✅ Using index scan - good for selective queries.")
                        elif "Bitmap" in plan_text:
                            suggestions.append("✅ Using bitmap scan - efficient for multiple matching rows.")
                        
                        # Filter conditions
                        filter_matches = re.findall(r'Filter:.*rows removed by filter:\s*(\d+)', plan_text)
                        if filter_matches:
                            removed = sum(int(r) for r in filter_matches)
                            if removed > 1000:
                                suggestions.append(f"⚠️  Filter removing {removed} rows. Consider more selective conditions or indexes.")
                        
                        # Sort operations
                        if "Sort" in plan_text:
                            sort_method = re.search(r'Sort Method:\s*(\w+)', plan_text)
                            if sort_method:
                                method = sort_method.group(1)
                                if method == "external":
                                    suggestions.append("⚠️  External sort (disk). Increase work_mem.")
                                else:
                                    suggestions.append(f"✅ In-memory sort ({method}).")
                        
                        if suggestions:
                            result += "\n".join(suggestions)
                        else:
                            result += "✅ No obvious performance issues detected."
                        
                        # Additional tips
                        result += "\n\n" + "-" * 50 + "\n💡 Tips:\n"
                        if not analyze:
                            result += "• Run with analyze=True to see actual execution times\n"
                        if analyze and not buffers:
                            result += "• Run with buffers=True to see buffer usage statistics\n"
                        result += "• Consider using EXPLAIN (VERBOSE) for more details"
                    
                    else:
                        # Return raw format (JSON, XML, YAML)
                        result = f"Execution Plan ({format_type} format):\n\n"
                        result += str(rows[0][0])
                    
                    return [types.TextContent(type="text", text=result)]
                    
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error analyzing query: {str(e)}"
            )]

    @staticmethod
    async def _execute_query_unsafe(db_url: str, query: str) -> dict:
        try:
            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    
                    # Get column names
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    
                    # Get rows
                    rows = cur.fetchall()
                    
                    if not rows:
                        return {"status": "success", "message": "Query executed successfully. No results returned.", "rows": []}
                    
                    # Format results
                    result = f"Query results ({len(rows)} rows):\n\n"
                    
                    # Add column headers
                    result += " | ".join(columns) + "\n"
                    result += "-" * (len(" | ".join(columns))) + "\n"
                    
                    # Add rows (limit to first 50 for readability)
                    for i, row in enumerate(rows[:50]):
                        result += " | ".join(str(val) for val in row) + "\n"
                    
                    if len(rows) > 50:
                        result += f"\n... and {len(rows) - 50} more rows"
                    
                    return {"status": "success", "message": result, "rows": rows}
                    
        except Exception as e:
            return {"status": "error", "message": f"Error executing query: {str(e)}"}
    
    @staticmethod
    async def handle_get_slow_queries(arguments: Dict[str, Any] | None) -> List[types.TextContent]:
        """
        Get slow queries from pg_stat_statements extension.
        """
        try:
            db_url = PostgresHandlers.get_connection_string()
            
            if not db_url:
                return [types.TextContent(
                    type="text",
                    text="Error: No database URL configured. Set DATABASE_URI environment variable."
                )]
            
            # Get parameters
            min_duration_ms = arguments.get("min_duration_ms", 1000) if arguments else 1000
            limit = arguments.get("limit", 20) if arguments else 20
            
            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    # First check if pg_stat_statements is available
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
                        )
                    """)
                    
                    extension_exists = cur.fetchone()[0]
                    
                    if not extension_exists:
                        # Try to enable it (requires superuser)
                        try:
                            cur.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")
                            conn.commit()
                        except Exception as ext_error:
                            return [types.TextContent(
                                type="text",
                                text=f"""pg_stat_statements extension is not available.

To enable slow query tracking, ask your database administrator to:
1. Add 'pg_stat_statements' to shared_preload_libraries in postgresql.conf
2. Restart PostgreSQL
3. Run: CREATE EXTENSION pg_stat_statements;

Error: {str(ext_error)}"""
                            )]
                    
                    # Query for slow queries
                    cur.execute("""
                        SELECT 
                            query,
                            calls,
                            total_exec_time as total_time_ms,
                            mean_exec_time as mean_time_ms,
                            min_exec_time as min_time_ms,
                            max_exec_time as max_time_ms,
                            stddev_exec_time as stddev_time_ms,
                            rows,
                            100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0) AS cache_hit_ratio
                        FROM pg_stat_statements
                        WHERE mean_exec_time > %s
                            AND query NOT LIKE 'EXPLAIN%%'
                            AND query NOT LIKE '%%pg_stat_statements%%'
                        ORDER BY mean_exec_time DESC
                        LIMIT %s
                    """, (min_duration_ms, limit))
                    
                    rows = cur.fetchall()
                    
                    if not rows:
                        return [types.TextContent(
                            type="text",
                            text=f"No queries found with mean execution time > {min_duration_ms}ms"
                        )]
                    
                    # Format results
                    result = f"Slow Queries Report (threshold: {min_duration_ms}ms)\n"
                    result += "=" * 80 + "\n\n"
                    
                    for idx, row in enumerate(rows, 1):
                        query = row[0]
                        calls = row[1]
                        total_time = row[2]
                        mean_time = row[3]
                        min_time = row[4]
                        max_time = row[5]
                        stddev_time = row[6]
                        total_rows = row[7]
                        cache_hit = row[8] or 0
                        
                        # Truncate long queries
                        if len(query) > 200:
                            query = query[:197] + "..."
                        
                        result += f"🔴 Query #{idx}\n"
                        result += f"Query: {query}\n"
                        result += f"Performance Stats:\n"
                        result += f"  • Calls: {calls:,}\n"
                        result += f"  • Mean Time: {mean_time:.2f} ms\n"
                        result += f"  • Total Time: {total_time:.2f} ms ({total_time/1000:.2f} seconds)\n"
                        result += f"  • Min/Max: {min_time:.2f} ms / {max_time:.2f} ms\n"
                        result += f"  • Std Dev: {stddev_time:.2f} ms\n"
                        result += f"  • Rows/Call: {total_rows/calls:.1f}\n"
                        result += f"  • Cache Hit: {cache_hit:.1f}%\n"
                        
                        # Analysis and suggestions
                        result += "\n📊 Analysis:\n"
                        suggestions = []
                        
                        # High variance
                        if stddev_time > mean_time * 0.5:
                            suggestions.append("• High variance in execution time - investigate data distribution")
                        
                        # Low cache hit
                        if cache_hit < 90:
                            suggestions.append(f"• Low cache hit ratio ({cache_hit:.1f}%) - consider increasing shared_buffers")
                        
                        # High row count
                        if total_rows / calls > 1000:
                            suggestions.append("• Returning many rows per call - consider pagination or more selective filters")
                        
                        # Frequent execution
                        if calls > 10000:
                            suggestions.append("• Very frequent execution - consider caching or query optimization")
                        
                        # Look for common patterns
                        query_upper = query.upper()
                        if "LIKE '%" in query_upper:
                            suggestions.append("• Leading wildcard in LIKE - cannot use index effectively")
                        
                        if "NOT IN" in query_upper or "NOT EXISTS" in query_upper:
                            suggestions.append("• NOT IN/EXISTS can be slow - consider LEFT JOIN with NULL check")
                        
                        if " OR " in query_upper:
                            suggestions.append("• OR conditions might prevent index usage - consider UNION")
                        
                        if "DISTINCT" in query_upper:
                            suggestions.append("• DISTINCT can be expensive - ensure proper indexes")
                        
                        if not suggestions:
                            suggestions.append("• Run EXPLAIN ANALYZE on this query for detailed analysis")
                        
                        result += "\n".join(suggestions)
                        result += "\n\n" + "-" * 80 + "\n\n"
                    
                    # Summary
                    result += f"\n📈 Summary:\n"
                    result += f"• Found {len(rows)} slow queries\n"
                    result += f"• Threshold: {min_duration_ms}ms mean execution time\n"
                    result += f"• Tip: Use explain-query tool to analyze specific queries in detail\n"
                    
                    return [types.TextContent(type="text", text=result)]
                    
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting slow queries: {str(e)}"
            )]
    
    @staticmethod
    async def handle_health_check(arguments: Dict[str, Any] | None) -> List[types.TextContent]:
        """
        Comprehensive health check of the PostgreSQL database.
        """
        try:
            db_url = PostgresHandlers.get_connection_string()
            
            if not db_url:
                return [types.TextContent(
                    type="text",
                    text="Error: No database URL configured. Set DATABASE_URI environment variable."
                )]
            
            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    result = "PostgreSQL Health Check Report\n"
                    result += "=" * 80 + "\n\n"
                    
                    # 1. Connection Stats
                    cur.execute("""
                        SELECT 
                            COUNT(*) FILTER (WHERE state = 'active') as active,
                            COUNT(*) FILTER (WHERE state = 'idle') as idle,
                            COUNT(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction,
                            COUNT(*) FILTER (WHERE wait_event IS NOT NULL) as waiting,
                            COUNT(*) as total,
                            (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
                        FROM pg_stat_activity
                        WHERE pid != pg_backend_pid()
                    """)
                    
                    conn_stats = cur.fetchone()
                    active, idle, idle_in_tx, waiting, total, max_conn = conn_stats
                    
                    result += "🔌 Connection Statistics:\n"
                    result += f"  • Active connections: {active}\n"
                    result += f"  • Idle connections: {idle}\n"
                    result += f"  • Idle in transaction: {idle_in_tx}\n"
                    result += f"  • Waiting connections: {waiting}\n"
                    result += f"  • Total connections: {total}/{max_conn} ({(total/max_conn)*100:.1f}% used)\n"
                    
                    # Connection warnings
                    if total / max_conn > 0.8:
                        result += "  ⚠️  WARNING: Connection usage above 80%!\n"
                    if idle_in_tx > 5:
                        result += "  ⚠️  WARNING: Many idle transactions - check for uncommitted transactions\n"
                    
                    result += "\n"
                    
                    # 2. Database Size and Growth
                    cur.execute("""
                        SELECT 
                            pg_database_size(current_database()) as db_size,
                            pg_size_pretty(pg_database_size(current_database())) as db_size_pretty
                    """)
                    
                    db_size, db_size_pretty = cur.fetchone()
                    
                    result += "💾 Database Size:\n"
                    result += f"  • Current size: {db_size_pretty}\n"
                    
                    # Get largest tables
                    cur.execute("""
                        SELECT 
                            schemaname || '.' || tablename as table_name,
                            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                        FROM pg_tables
                        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                        LIMIT 5
                    """)
                    
                    largest_tables = cur.fetchall()
                    if largest_tables:
                        result += "  • Top 5 largest tables:\n"
                        for table, size in largest_tables:
                            result += f"    - {table}: {size}\n"
                    
                    result += "\n"
                    
                    # 3. Cache Hit Ratio
                    cur.execute("""
                        SELECT 
                            sum(blks_hit)::float / NULLIF(sum(blks_hit + blks_read), 0) * 100 as cache_hit_ratio
                        FROM pg_stat_database
                        WHERE datname = current_database()
                    """)
                    
                    cache_hit_ratio = cur.fetchone()[0] or 0
                    
                    result += "🎯 Cache Performance:\n"
                    result += f"  • Cache hit ratio: {cache_hit_ratio:.2f}%\n"
                    
                    if cache_hit_ratio < 90:
                        result += "  ⚠️  WARNING: Cache hit ratio below 90% - consider increasing shared_buffers\n"
                    elif cache_hit_ratio >= 99:
                        result += "  ✅ Excellent cache performance\n"
                    else:
                        result += "  ✅ Good cache performance\n"
                    
                    result += "\n"
                    
                    # 4. Vacuum and Maintenance
                    cur.execute("""
                        SELECT 
                            schemaname,
                            tablename,
                            last_vacuum,
                            last_autovacuum,
                            last_analyze,
                            last_autoanalyze,
                            n_dead_tup,
                            n_live_tup,
                            CASE 
                                WHEN n_live_tup > 0 
                                THEN round((n_dead_tup::numeric / n_live_tup) * 100, 2)
                                ELSE 0
                            END as dead_tup_ratio
                        FROM pg_stat_user_tables
                        WHERE n_dead_tup > 1000
                        ORDER BY n_dead_tup DESC
                        LIMIT 5
                    """)
                    
                    vacuum_stats = cur.fetchall()
                    
                    result += "🧹 Vacuum/Maintenance Status:\n"
                    if vacuum_stats:
                        result += "  • Tables with high dead tuple count:\n"
                        for row in vacuum_stats:
                            schema, table, last_vac, last_auto_vac, _, _, dead, live, ratio = row
                            result += f"    - {schema}.{table}: {dead:,} dead tuples ({ratio}% of live)\n"
                            if ratio > 20:
                                result += f"      ⚠️  Consider manual VACUUM\n"
                    else:
                        result += "  ✅ No tables with significant dead tuples\n"
                    
                    result += "\n"
                    
                    # 5. Replication Status (if any)
                    cur.execute("""
                        SELECT 
                            COUNT(*) as replica_count,
                            MAX(replay_lag) as max_lag
                        FROM pg_stat_replication
                    """)
                    
                    replica_count, max_lag = cur.fetchone()
                    
                    if replica_count and replica_count > 0:
                        result += "🔄 Replication Status:\n"
                        result += f"  • Active replicas: {replica_count}\n"
                        if max_lag:
                            result += f"  • Maximum lag: {max_lag}\n"
                            if max_lag.total_seconds() > 60:
                                result += "  ⚠️  WARNING: Replication lag exceeds 1 minute\n"
                        else:
                            result += "  ✅ All replicas in sync\n"
                        result += "\n"
                    
                    # 6. Long Running Queries
                    cur.execute("""
                        SELECT 
                            pid,
                            now() - pg_stat_activity.query_start AS duration,
                            query
                        FROM pg_stat_activity
                        WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
                            AND state = 'active'
                            AND query NOT LIKE '%pg_stat_activity%'
                        ORDER BY duration DESC
                        LIMIT 3
                    """)
                    
                    long_queries = cur.fetchall()
                    
                    if long_queries:
                        result += "⏱️  Long Running Queries:\n"
                        for pid, duration, query in long_queries:
                            query_short = query[:100] + "..." if len(query) > 100 else query
                            result += f"  • PID {pid}: Running for {duration}\n"
                            result += f"    Query: {query_short}\n"
                        result += "  ⚠️  Consider investigating these queries\n"
                        result += "\n"
                    
                    # 7. Table Bloat Check
                    cur.execute("""
                        SELECT 
                            schemaname || '.' || tablename as table_name,
                            pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                            round(
                                100 * pg_relation_size(schemaname||'.'||tablename) / 
                                NULLIF(pg_total_relation_size(schemaname||'.'||tablename), 0)
                            ) as table_ratio
                        FROM pg_tables
                        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                            AND pg_relation_size(schemaname||'.'||tablename) > 10485760  -- 10MB
                        ORDER BY table_ratio ASC
                        LIMIT 5
                    """)
                    
                    bloat_candidates = cur.fetchall()
                    
                    bloated_tables = []
                    for table, size, ratio in bloat_candidates:
                        if ratio and ratio < 50:  # Table is less than 50% of total size (rest is indexes/toast)
                            bloated_tables.append((table, size, ratio))
                    
                    if bloated_tables:
                        result += "🎈 Potential Table Bloat:\n"
                        for table, size, ratio in bloated_tables:
                            result += f"  • {table}: {size} ({ratio}% of total relation size)\n"
                        result += "  💡 Low ratios may indicate index bloat\n"
                        result += "\n"
                    
                    # 8. Summary and Recommendations
                    result += "📊 Overall Health Summary:\n"
                    
                    health_score = 100
                    issues = []
                    
                    if total / max_conn > 0.8:
                        health_score -= 10
                        issues.append("High connection usage")
                    
                    if cache_hit_ratio < 90:
                        health_score -= 20
                        issues.append("Low cache hit ratio")
                    
                    if idle_in_tx > 5:
                        health_score -= 10
                        issues.append("Many idle transactions")
                    
                    if long_queries:
                        health_score -= 10
                        issues.append("Long running queries detected")
                    
                    if vacuum_stats:
                        health_score -= 5
                        issues.append("Tables need vacuum")
                    
                    if health_score >= 90:
                        result += f"  • Health Score: {health_score}/100 ✅ EXCELLENT\n"
                    elif health_score >= 70:
                        result += f"  • Health Score: {health_score}/100 ⚠️  GOOD (needs attention)\n"
                    else:
                        result += f"  • Health Score: {health_score}/100 🔴 POOR (immediate action needed)\n"
                    
                    if issues:
                        result += "  • Issues found:\n"
                        for issue in issues:
                            result += f"    - {issue}\n"
                    else:
                        result += "  • No major issues detected\n"
                    
                    result += "\n💡 Next Steps:\n"
                    result += "• Use get-slow-queries to identify performance bottlenecks\n"
                    result += "• Use explain-query to analyze problematic queries\n"
                    result += "• Monitor this health check regularly\n"
                    
                    return [types.TextContent(type="text", text=result)]
                    
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error performing health check: {str(e)}"
            )]

