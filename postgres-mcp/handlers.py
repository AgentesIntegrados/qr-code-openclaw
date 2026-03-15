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

    
    @staticmethod
    async def handle_suggest_indexes(arguments: Dict[str, Any] | None) -> List[types.TextContent]:
        """Analyze query workload and suggest optimal indexes."""
        
        # Default parameters
        arguments = arguments or {}
        min_calls = arguments.get("min_calls", 10)  # Minimum calls to consider query
        min_duration_ms = arguments.get("min_duration_ms", 100)  # Minimum avg duration
        limit = arguments.get("limit", 10)  # Top queries to analyze
        
        try:
            # Use sync psycopg for better compatibility
            import psycopg
            
            # Get database URI from environment
            db_uri = os.environ.get("DATABASE_URI")
            if not db_uri:
                return [types.TextContent(
                    type="text",
                    text="Error: DATABASE_URI environment variable not set"
                )]
            
            with psycopg.connect(db_uri) as conn:
                with conn.cursor() as cur:
                    result = "🔍 INDEX SUGGESTION ANALYSIS\n" + "="*50 + "\n\n"
                    
                    # Check if pg_stat_statements is available
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
                        )
                    """)
                    
                    if not cur.fetchone()[0]:
                        result += "⚠️  Warning: pg_stat_statements extension not installed.\n"
                        result += "To enable query workload analysis:\n"
                        result += "  1. Add to postgresql.conf: shared_preload_libraries = 'pg_stat_statements'\n"
                        result += "  2. Restart PostgreSQL\n"
                        result += "  3. Run: CREATE EXTENSION pg_stat_statements;\n\n"
                        
                        # Fallback: analyze table structure for basic suggestions
                        result += "📊 Falling back to table structure analysis...\n\n"
                        
                        # Find tables without primary keys
                        cur.execute("""
                            SELECT 
                                schemaname,
                                tablename
                            FROM pg_tables t
                            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                            AND NOT EXISTS (
                                SELECT 1 
                                FROM pg_indexes i 
                                WHERE i.schemaname = t.schemaname 
                                AND i.tablename = t.tablename 
                                AND i.indexname LIKE '%_pkey'
                            )
                        """)
                        
                        tables_without_pk = cur.fetchall()
                        if tables_without_pk:
                            result += "🔴 Tables without Primary Keys:\n"
                            for schema, table in tables_without_pk:
                                result += f"  • {schema}.{table}\n"
                                result += f"    SUGGESTION: Add primary key to ensure data integrity\n"
                            result += "\n"
                        
                        # Find foreign key columns without indexes
                        cur.execute("""
                            SELECT DISTINCT
                                tc.table_schema,
                                tc.table_name,
                                kcu.column_name,
                                ccu.table_schema AS foreign_table_schema,
                                ccu.table_name AS foreign_table_name
                            FROM information_schema.table_constraints AS tc
                            JOIN information_schema.key_column_usage AS kcu
                                ON tc.constraint_name = kcu.constraint_name
                                AND tc.table_schema = kcu.table_schema
                            JOIN information_schema.constraint_column_usage AS ccu
                                ON ccu.constraint_name = tc.constraint_name
                                AND ccu.table_schema = tc.table_schema
                            WHERE tc.constraint_type = 'FOREIGN KEY'
                            AND NOT EXISTS (
                                SELECT 1
                                FROM pg_indexes i
                                WHERE i.schemaname = tc.table_schema
                                AND i.tablename = tc.table_name
                                AND i.indexdef LIKE '%' || kcu.column_name || '%'
                            )
                        """)
                        
                        fk_without_index = cur.fetchall()
                        if fk_without_index:
                            result += "🟡 Foreign Keys without Indexes:\n"
                            for schema, table, column, fk_schema, fk_table in fk_without_index:
                                result += f"  • {schema}.{table}.{column} → {fk_schema}.{fk_table}\n"
                                result += f"    SUGGESTION: CREATE INDEX idx_{table}_{column} ON {schema}.{table}({column});\n"
                            result += "\n"
                    
                    else:
                        # Analyze query workload from pg_stat_statements
                        result += "📊 Analyzing Query Workload...\n\n"
                        
                        # Get top time-consuming queries
                        cur.execute(f"""
                            SELECT 
                                query,
                                calls,
                                mean_exec_time,
                                total_exec_time,
                                min_exec_time,
                                max_exec_time,
                                stddev_exec_time,
                                rows
                            FROM pg_stat_statements
                            WHERE query NOT LIKE '%pg_stat_statements%'
                            AND query NOT LIKE 'COMMIT%'
                            AND query NOT LIKE 'BEGIN%'
                            AND query NOT LIKE 'SET%'
                            AND calls >= %s
                            AND mean_exec_time >= %s
                            ORDER BY total_exec_time DESC
                            LIMIT %s
                        """, (min_calls, min_duration_ms, limit))
                        
                        queries = cur.fetchall()
                        
                        if not queries:
                            result += "No queries found matching criteria.\n"
                            result += f"Try lowering min_calls ({min_calls}) or min_duration_ms ({min_duration_ms})\n"
                        else:
                            suggestions = []
                            
                            for idx, (query, calls, mean_time, total_time, min_time, max_time, stddev_time, rows) in enumerate(queries, 1):
                                result += f"Query #{idx}:\n"
                                result += f"  Calls: {calls:,} | Avg: {mean_time:.2f}ms | Total: {total_time/1000:.2f}s\n"
                                result += f"  Query: {query[:100]}{'...' if len(query) > 100 else ''}\n"
                                
                                # Analyze query patterns for index suggestions
                                query_lower = query.lower()
                                
                                # Pattern 1: WHERE clauses without indexes
                                if 'where' in query_lower:
                                    # Try to extract table and column from WHERE clause
                                    import re
                                    
                                    # Look for patterns like "table.column = " or "table.column LIKE"
                                    where_patterns = [
                                        r'where\s+(\w+)\.(\w+)\s*=',
                                        r'where\s+(\w+)\.(\w+)\s*like',
                                        r'where\s+(\w+)\.(\w+)\s*in',
                                        r'where\s+(\w+)\.(\w+)\s*between',
                                        r'and\s+(\w+)\.(\w+)\s*=',
                                        r'and\s+(\w+)\.(\w+)\s*like',
                                    ]
                                    
                                    for pattern in where_patterns:
                                        matches = re.findall(pattern, query_lower)
                                        for table, column in matches:
                                            # Check if index exists
                                            cur.execute("""
                                                SELECT COUNT(*) 
                                                FROM pg_indexes 
                                                WHERE tablename = %s 
                                                AND indexdef LIKE %s
                                            """, (table, f'%{column}%'))
                                            
                                            if cur.fetchone()[0] == 0:
                                                suggestion = f"CREATE INDEX idx_{table}_{column} ON {table}({column});"
                                                if suggestion not in suggestions:
                                                    suggestions.append(suggestion)
                                                    result += f"  💡 Missing index on {table}.{column}\n"
                                
                                # Pattern 2: JOIN operations
                                if 'join' in query_lower:
                                    join_patterns = [
                                        r'join\s+(\w+)\s+\w+\s+on\s+\w+\.(\w+)\s*=\s*\w+\.(\w+)',
                                        r'join\s+(\w+)\s+on\s+\w+\.(\w+)\s*=\s*\w+\.(\w+)',
                                    ]
                                    
                                    for pattern in join_patterns:
                                        matches = re.findall(pattern, query_lower)
                                        for match in matches:
                                            result += f"  💡 JOIN detected - ensure indexes on join columns\n"
                                            break
                                
                                # Pattern 3: ORDER BY without index
                                if 'order by' in query_lower:
                                    order_patterns = [
                                        r'order\s+by\s+(\w+)\.(\w+)',
                                        r'order\s+by\s+(\w+)\s+',
                                    ]
                                    
                                    for pattern in order_patterns:
                                        matches = re.findall(pattern, query_lower)
                                        if matches:
                                            result += f"  💡 ORDER BY detected - consider index for sorting\n"
                                            break
                                
                                # Pattern 4: LIKE patterns
                                if 'like' in query_lower and ('%' in query or '_' in query):
                                    if query_lower.count('like') > 0:
                                        like_pattern = re.search(r"like\s+'([^']*)'", query_lower)
                                        if like_pattern:
                                            pattern_value = like_pattern.group(1)
                                            if pattern_value.startswith('%'):
                                                result += f"  ⚠️  Leading wildcard pattern detected - consider full-text search\n"
                                            else:
                                                result += f"  💡 LIKE pattern - consider prefix index\n"
                                
                                result += "\n"
                            
                            # Show consolidated suggestions
                            if suggestions:
                                result += "\n🎯 RECOMMENDED INDEXES:\n"
                                result += "-" * 50 + "\n"
                                for suggestion in suggestions[:10]:  # Limit to 10 suggestions
                                    result += f"{suggestion}\n"
                                
                                result += "\n⚠️  Important Notes:\n"
                                result += "• Test these indexes in a development environment first\n"
                                result += "• Monitor index size and maintenance overhead\n"
                                result += "• Consider using CONCURRENTLY for production: CREATE INDEX CONCURRENTLY ...\n"
                                result += "• Run ANALYZE after creating indexes\n"
                    
                    # General recommendations
                    result += "\n📚 Best Practices:\n"
                    result += "• Keep indexes focused (avoid too many columns)\n"
                    result += "• Consider partial indexes for filtered queries\n"
                    result += "• Use INCLUDE clause for covering indexes (PostgreSQL 11+)\n"
                    result += "• Monitor unused indexes with analyze-index-usage tool\n"
                    result += "• Regular VACUUM and ANALYZE for accurate statistics\n"
                    
                    return [types.TextContent(type="text", text=result)]
                    
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error analyzing indexes: {str(e)}"
            )]
    
    @staticmethod
    async def handle_get_table_stats(arguments: Dict[str, Any] | None) -> List[types.TextContent]:
        """Get detailed statistics for database tables."""
        
        # Default parameters
        arguments = arguments or {}
        schema = arguments.get("schema", "public")
        table_pattern = arguments.get("table_pattern", "%")  # SQL LIKE pattern
        include_toast = arguments.get("include_toast", False)
        include_indexes = arguments.get("include_indexes", True)
        
        try:
            # Use sync psycopg for better compatibility
            import psycopg
            
            # Get database URI from environment
            db_uri = os.environ.get("DATABASE_URI")
            if not db_uri:
                return [types.TextContent(
                    type="text",
                    text="Error: DATABASE_URI environment variable not set"
                )]
            
            with psycopg.connect(db_uri) as conn:
                with conn.cursor() as cur:
                    result = "📊 TABLE STATISTICS ANALYSIS\n" + "="*50 + "\n\n"
                    
                    # Get table statistics
                    cur.execute("""
                        WITH table_stats AS (
                            SELECT 
                                n.nspname AS schema_name,
                                c.relname AS table_name,
                                c.reltuples AS row_estimate,
                                pg_table_size(c.oid) AS table_size,
                                pg_indexes_size(c.oid) AS indexes_size,
                                pg_total_relation_size(c.oid) AS total_size,
                                COALESCE(toast.reltuples, 0) AS toast_rows,
                                COALESCE(pg_table_size(toast.oid), 0) AS toast_size,
                                obj_description(c.oid, 'pg_class') AS description,
                                age(c.relfrozenxid) AS xid_age,
                                c.relkind
                            FROM pg_class c
                            JOIN pg_namespace n ON n.oid = c.relnamespace
                            LEFT JOIN pg_class toast ON c.reltoastrelid = toast.oid
                            WHERE c.relkind IN ('r', 'p')  -- regular tables and partitioned tables
                            AND n.nspname = %s
                            AND c.relname LIKE %s
                        ),
                        index_stats AS (
                            SELECT 
                                schemaname,
                                tablename,
                                COUNT(*) AS index_count,
                                SUM(pg_relation_size(indexrelid)) AS total_index_size
                            FROM pg_indexes
                            JOIN pg_class ON pg_class.relname = indexname
                            WHERE schemaname = %s
                            AND tablename LIKE %s
                            GROUP BY schemaname, tablename
                        ),
                        stats_summary AS (
                            SELECT 
                                schemaname,
                                tablename,
                                n_tup_ins,
                                n_tup_upd,
                                n_tup_del,
                                n_tup_hot_upd,
                                n_live_tup,
                                n_dead_tup,
                                n_mod_since_analyze,
                                last_vacuum,
                                last_autovacuum,
                                last_analyze,
                                last_autoanalyze,
                                vacuum_count,
                                autovacuum_count,
                                analyze_count,
                                autoanalyze_count
                            FROM pg_stat_user_tables
                            WHERE schemaname = %s
                            AND tablename LIKE %s
                        )
                        SELECT 
                            t.*,
                            i.index_count,
                            i.total_index_size,
                            s.*
                        FROM table_stats t
                        LEFT JOIN index_stats i ON t.schema_name = i.schemaname AND t.table_name = i.tablename
                        LEFT JOIN stats_summary s ON t.schema_name = s.schemaname AND t.table_name = s.tablename
                        ORDER BY t.total_size DESC
                    """, (schema, table_pattern, schema, table_pattern, schema, table_pattern))
                    
                    tables = cur.fetchall()
                    
                    if not tables:
                        result += f"No tables found matching pattern '{table_pattern}' in schema '{schema}'\n"
                    else:
                        total_size = 0
                        total_rows = 0
                        
                        for table in tables:
                            (schema_name, table_name, row_estimate, table_size, indexes_size, 
                             total_table_size, toast_rows, toast_size, description, xid_age, relkind,
                             index_count, total_index_size, n_tup_ins, n_tup_upd, n_tup_del,
                             n_tup_hot_upd, n_live_tup, n_dead_tup, n_mod_since_analyze,
                             last_vacuum, last_autovacuum, last_analyze, last_autoanalyze,
                             vacuum_count, autovacuum_count, analyze_count, autoanalyze_count) = table
                            
                            total_size += total_table_size or 0
                            total_rows += row_estimate or 0
                            
                            result += f"📋 Table: {schema_name}.{table_name}\n"
                            result += "-" * 50 + "\n"
                            
                            # Basic info
                            if description:
                                result += f"Description: {description}\n"
                            
                            result += f"Type: {'Partitioned Table' if relkind == 'p' else 'Regular Table'}\n"
                            result += f"Estimated Rows: {int(row_estimate):,}\n"
                            
                            # Size information
                            result += f"\n💾 Storage:\n"
                            result += f"  • Table Size: {PostgresHandlers._format_bytes(table_size)}\n"
                            if indexes_size:
                                result += f"  • Indexes Size: {PostgresHandlers._format_bytes(indexes_size)}\n"
                            if toast_size and include_toast:
                                result += f"  • TOAST Size: {PostgresHandlers._format_bytes(toast_size)}\n"
                                result += f"  • TOAST Rows: {int(toast_rows):,}\n"
                            result += f"  • Total Size: {PostgresHandlers._format_bytes(total_table_size)}\n"
                            
                            # Index information
                            if include_indexes and index_count:
                                result += f"\n🔍 Indexes:\n"
                                result += f"  • Count: {index_count or 0}\n"
                                result += f"  • Total Size: {PostgresHandlers._format_bytes(total_index_size or 0)}\n"
                                
                                # Get individual indexes
                                cur.execute("""
                                    SELECT 
                                        indexname,
                                        pg_size_pretty(pg_relation_size(i.indexrelid)) AS size,
                                        idx_scan,
                                        idx_tup_read,
                                        idx_tup_fetch
                                    FROM pg_indexes
                                    JOIN pg_stat_user_indexes i ON i.indexrelname = indexname
                                    WHERE schemaname = %s AND tablename = %s
                                    ORDER BY pg_relation_size(i.indexrelid) DESC
                                """, (schema_name, table_name))
                                
                                indexes = cur.fetchall()
                                for idx_name, idx_size, idx_scan, idx_tup_read, idx_tup_fetch in indexes:
                                    result += f"    - {idx_name}: {idx_size} (scans: {idx_scan:,})\n"
                            
                            # Activity statistics
                            if n_live_tup is not None:
                                result += f"\n📈 Activity:\n"
                                result += f"  • Live Tuples: {n_live_tup:,}\n"
                                result += f"  • Dead Tuples: {n_dead_tup:,}\n"
                                
                                # Calculate bloat estimate
                                if n_live_tup > 0:
                                    bloat_ratio = (n_dead_tup / n_live_tup) * 100
                                    if bloat_ratio > 20:
                                        result += f"  • ⚠️  Bloat Ratio: {bloat_ratio:.1f}% (consider VACUUM)\n"
                                    else:
                                        result += f"  • Bloat Ratio: {bloat_ratio:.1f}%\n"
                                
                                result += f"  • Inserts: {n_tup_ins:,}\n"
                                result += f"  • Updates: {n_tup_upd:,}\n"
                                result += f"  • Deletes: {n_tup_del:,}\n"
                                
                                if n_tup_upd > 0:
                                    hot_ratio = (n_tup_hot_upd / n_tup_upd) * 100
                                    result += f"  • HOT Update Ratio: {hot_ratio:.1f}%\n"
                            
                            # Maintenance information
                            result += f"\n🔧 Maintenance:\n"
                            if last_vacuum:
                                result += f"  • Last Vacuum: {last_vacuum}\n"
                            if last_autovacuum:
                                result += f"  • Last Autovacuum: {last_autovacuum}\n"
                            if last_analyze:
                                result += f"  • Last Analyze: {last_analyze}\n"
                            if last_autoanalyze:
                                result += f"  • Last Autoanalyze: {last_autoanalyze}\n"
                            
                            if n_mod_since_analyze and n_mod_since_analyze > 0:
                                result += f"  • ⚠️  Modifications since analyze: {n_mod_since_analyze:,}\n"
                            
                            # Transaction ID age warning
                            if xid_age > 1000000000:
                                result += f"  • 🔴 XID Age: {xid_age:,} (VACUUM FREEZE needed!)\n"
                            elif xid_age > 500000000:
                                result += f"  • ⚠️  XID Age: {xid_age:,} (plan VACUUM FREEZE)\n"
                            
                            result += "\n"
                        
                        # Summary
                        result += "📊 SUMMARY\n"
                        result += "="*50 + "\n"
                        result += f"Total Tables: {len(tables)}\n"
                        result += f"Total Rows: {int(total_rows):,}\n"
                        result += f"Total Size: {PostgresHandlers._format_bytes(total_size)}\n"
                        
                        # Recommendations
                        result += "\n💡 Recommendations:\n"
                        
                        # Find tables that need maintenance
                        tables_need_vacuum = []
                        tables_need_analyze = []
                        tables_high_bloat = []
                        
                        for table in tables:
                            table_name = table[1]
                            n_dead_tup = table[18]
                            n_live_tup = table[17]
                            n_mod_since_analyze = table[19]
                            
                            if n_live_tup and n_dead_tup and n_dead_tup / n_live_tup > 0.2:
                                tables_high_bloat.append(table_name)
                            
                            if n_mod_since_analyze and n_mod_since_analyze > n_live_tup * 0.1:
                                tables_need_analyze.append(table_name)
                        
                        if tables_high_bloat:
                            result += f"• Tables with high bloat: {', '.join(tables_high_bloat)}\n"
                            result += "  Run: VACUUM (VERBOSE, ANALYZE) table_name;\n"
                        
                        if tables_need_analyze:
                            result += f"• Tables needing ANALYZE: {', '.join(tables_need_analyze)}\n"
                            result += "  Run: ANALYZE table_name;\n"
                        
                        if not tables_high_bloat and not tables_need_analyze:
                            result += "• All tables appear well-maintained\n"
                    
                    return [types.TextContent(type="text", text=result)]
                    
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting table statistics: {str(e)}"
            )]
    
    @staticmethod
    def _format_bytes(size_bytes):
        """Format bytes to human readable format."""
        if size_bytes is None:
            return "0 B"
        
        size_bytes = int(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.2f} PB"
    @staticmethod
    async def handle_analyze_index_usage(arguments: Dict[str, Any] | None) -> List[types.TextContent]:
        """Analyze index usage and identify unused or redundant indexes."""
        
        # Default parameters
        arguments = arguments or {}
        schema = arguments.get("schema", "public")
        min_size_mb = arguments.get("min_size_mb", 1)  # Minimum size to consider
        days_unused = arguments.get("days_unused", 30)  # Days without use to flag
        
        try:
            # Use sync psycopg for better compatibility
            import psycopg
            from datetime import datetime, timedelta
            
            # Get database URI from environment
            db_uri = os.environ.get("DATABASE_URI")
            if not db_uri:
                return [types.TextContent(
                    type="text",
                    text="Error: DATABASE_URI environment variable not set"
                )]
            
            with psycopg.connect(db_uri) as conn:
                with conn.cursor() as cur:
                    result = "🔍 INDEX USAGE ANALYSIS\n" + "="*50 + "\n\n"
                    
                    # Get all indexes with their usage statistics
                    cur.execute("""
                        SELECT 
                            n.nspname AS schema_name,
                            t.relname AS table_name,
                            i.relname AS index_name,
                            x.indisprimary AS is_primary,
                            x.indisunique AS is_unique,
                            pg_relation_size(i.oid) AS index_size,
                            pg_size_pretty(pg_relation_size(i.oid)) AS index_size_pretty,
                            COALESCE(s.idx_scan, 0) AS index_scans,
                            COALESCE(s.idx_tup_read, 0) AS tuples_read,
                            COALESCE(s.idx_tup_fetch, 0) AS tuples_fetched,
                            pg_stat_file(pg_relation_filepath(i.oid)).modification AS last_modified,
                            array_to_string(
                                ARRAY(
                                    SELECT pg_get_indexdef(i.oid, k.i, true)
                                    FROM generate_subscripts(x.indkey, 1) AS k(i)
                                ),
                                ', '
                            ) AS index_columns,
                            pg_get_indexdef(i.oid) AS index_definition
                        FROM pg_index x
                        JOIN pg_class i ON i.oid = x.indexrelid
                        JOIN pg_class t ON t.oid = x.indrelid
                        JOIN pg_namespace n ON n.oid = i.relnamespace
                        LEFT JOIN pg_stat_user_indexes s ON s.indexrelid = x.indexrelid
                        WHERE n.nspname = %s
                        AND i.relkind = 'i'
                        AND pg_relation_size(i.oid) >= %s * 1024 * 1024  -- Size filter
                        ORDER BY 
                            CASE WHEN COALESCE(s.idx_scan, 0) = 0 THEN 0 ELSE 1 END,
                            pg_relation_size(i.oid) DESC
                    """, (schema, min_size_mb))
                    
                    indexes = cur.fetchall()
                    
                    if not indexes:
                        result += f"No indexes found in schema '{schema}' larger than {min_size_mb}MB\n"
                    else:
                        # Categorize indexes
                        unused_indexes = []
                        rarely_used_indexes = []
                        duplicate_indexes = {}
                        oversized_indexes = []
                        
                        # Track column combinations for duplicate detection
                        column_combinations = {}
                        
                        total_index_size = 0
                        unused_size = 0
                        
                        for idx in indexes:
                            (schema_name, table_name, index_name, is_primary, is_unique,
                             index_size, index_size_pretty, index_scans, tuples_read,
                             tuples_fetched, last_modified, index_columns, index_definition) = idx
                            
                            total_index_size += index_size
                            
                            # Check for unused indexes
                            if index_scans == 0 and not is_primary:
                                unused_indexes.append(idx)
                                unused_size += index_size
                            elif index_scans < 100 and not is_primary and not is_unique:
                                rarely_used_indexes.append(idx)
                            
                            # Check for duplicate indexes (same columns on same table)
                            table_key = f"{schema_name}.{table_name}"
                            if table_key not in column_combinations:
                                column_combinations[table_key] = {}
                            
                            if index_columns in column_combinations[table_key]:
                                if table_key not in duplicate_indexes:
                                    duplicate_indexes[table_key] = []
                                duplicate_indexes[table_key].append({
                                    'index1': column_combinations[table_key][index_columns],
                                    'index2': index_name,
                                    'columns': index_columns
                                })
                            else:
                                column_combinations[table_key][index_columns] = index_name
                            
                            # Check for oversized indexes (larger than table)
                            cur.execute("""
                                SELECT pg_relation_size(%s::regclass)
                            """, (f'{schema_name}."{table_name}"',))
                            table_size = cur.fetchone()[0]
                            
                            if index_size > table_size * 0.5 and not is_primary:
                                oversized_indexes.append({
                                    'index': idx,
                                    'table_size': table_size,
                                    'ratio': index_size / table_size if table_size > 0 else 0
                                })
                        
                        # Report findings
                        result += f"📊 Summary:\n"
                        result += f"  • Total indexes analyzed: {len(indexes)}\n"
                        result += f"  • Total index size: {PostgresExtendedHandlers._format_bytes(total_index_size)}\n"
                        result += f"  • Unused indexes: {len(unused_indexes)}\n"
                        result += f"  • Unused size: {PostgresExtendedHandlers._format_bytes(unused_size)}\n\n"
                        
                        # Unused indexes section
                        if unused_indexes:
                            result += "🔴 UNUSED INDEXES (Never scanned):\n"
                            result += "-" * 50 + "\n"
                            for idx in unused_indexes[:10]:  # Limit display
                                schema_name, table_name, index_name, _, _, size, size_pretty, _, _, _, _, columns, _ = idx
                                result += f"• {schema_name}.{index_name} on {table_name}\n"
                                result += f"  Size: {size_pretty}\n"
                                result += f"  Columns: {columns}\n"
                                result += f"  💡 Action: DROP INDEX IF EXISTS {schema_name}.{index_name};\n\n"
                            
                            if len(unused_indexes) > 10:
                                result += f"... and {len(unused_indexes) - 10} more unused indexes\n\n"
                        
                        # Rarely used indexes section
                        if rarely_used_indexes:
                            result += "🟡 RARELY USED INDEXES (< 100 scans):\n"
                            result += "-" * 50 + "\n"
                            for idx in rarely_used_indexes[:5]:
                                schema_name, table_name, index_name, _, _, size, size_pretty, scans, _, _, _, columns, _ = idx
                                result += f"• {schema_name}.{index_name} on {table_name}\n"
                                result += f"  Size: {size_pretty} | Scans: {scans}\n"
                                result += f"  Columns: {columns}\n"
                                result += f"  💡 Consider removing if not needed for uniqueness\n\n"
                        
                        # Duplicate indexes section
                        if duplicate_indexes:
                            result += "🔄 DUPLICATE INDEXES (Same columns):\n"
                            result += "-" * 50 + "\n"
                            for table, duplicates in duplicate_indexes.items():
                                result += f"Table: {table}\n"
                                for dup in duplicates:
                                    result += f"  • {dup['index1']} ≈ {dup['index2']}\n"
                                    result += f"    Columns: {dup['columns']}\n"
                                    result += f"    💡 Consider keeping only one\n"
                                result += "\n"
                        
                        # Oversized indexes section
                        if oversized_indexes:
                            result += "📏 OVERSIZED INDEXES (> 50% of table size):\n"
                            result += "-" * 50 + "\n"
                            for item in oversized_indexes[:5]:
                                idx = item['index']
                                ratio = item['ratio']
                                schema_name, table_name, index_name, _, _, size, size_pretty, _, _, _, _, _, _ = idx
                                result += f"• {schema_name}.{index_name} on {table_name}\n"
                                result += f"  Index: {size_pretty} | Ratio: {ratio:.1f}x table size\n"
                                result += f"  💡 Review if all columns are necessary\n\n"
                        
                        # Best practices section
                        result += "📚 BEST PRACTICES:\n"
                        result += "-" * 50 + "\n"
                        result += "• Remove unused indexes to save space and improve write performance\n"
                        result += "• Consolidate duplicate indexes\n"
                        result += "• Use partial indexes for filtered queries\n"
                        result += "• Consider multi-column indexes for common query patterns\n"
                        result += "• Monitor pg_stat_user_indexes regularly\n\n"
                        
                        # Savings calculation
                        if unused_size > 0:
                            result += "💰 POTENTIAL SAVINGS:\n"
                            result += f"Removing unused indexes would free up: {PostgresExtendedHandlers._format_bytes(unused_size)}\n"
                            result += f"This is {(unused_size / total_index_size * 100):.1f}% of total index space\n"
                    
                    return [types.TextContent(type="text", text=result)]
                    
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error analyzing index usage: {str(e)}"
            )]
    @staticmethod
    async def handle_get_blocking_queries(arguments: Dict[str, Any] | None) -> List[types.TextContent]:
        """Detect queries that are blocking other queries."""
        
        # Default parameters
        arguments = arguments or {}
        include_locks = arguments.get("include_locks", True)
        min_duration_ms = arguments.get("min_duration_ms", 1000)
        
        try:
            # Use sync psycopg for better compatibility
            import psycopg
            from datetime import datetime
            
            # Get database URI from environment
            db_uri = os.environ.get("DATABASE_URI")
            if not db_uri:
                return [types.TextContent(
                    type="text",
                    text="Error: DATABASE_URI environment variable not set"
                )]
            
            with psycopg.connect(db_uri) as conn:
                with conn.cursor() as cur:
                    result = "🔒 BLOCKING QUERIES ANALYSIS\n" + "="*50 + "\n\n"
                    
                    # Get PostgreSQL version for compatibility
                    cur.execute("SELECT version()")
                    pg_version = cur.fetchone()[0]
                    result += f"PostgreSQL Version: {pg_version.split(',')[0]}\n\n"
                    
                    # Check for blocking queries
                    cur.execute("""
                        WITH blocking_tree AS (
                            SELECT 
                                blocking.pid AS blocking_pid,
                                blocking.usename AS blocking_user,
                                blocking.application_name AS blocking_app,
                                blocking.client_addr AS blocking_client,
                                blocking.query_start AS blocking_query_start,
                                blocking.state AS blocking_state,
                                blocking.query AS blocking_query,
                                blocked.pid AS blocked_pid,
                                blocked.usename AS blocked_user,
                                blocked.application_name AS blocked_app,
                                blocked.client_addr AS blocked_client,
                                blocked.query_start AS blocked_query_start,
                                blocked.state AS blocked_state,
                                blocked.query AS blocked_query,
                                (NOW() - blocking.query_start) AS blocking_duration,
                                (NOW() - blocked.query_start) AS blocked_duration
                            FROM pg_stat_activity blocking
                            JOIN pg_stat_activity blocked 
                                ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
                            WHERE blocking.pid != blocked.pid
                        )
                        SELECT * FROM blocking_tree
                        ORDER BY blocking_duration DESC
                    """)
                    
                    blocking_queries = cur.fetchall()
                    
                    if not blocking_queries:
                        result += "✅ No blocking queries detected!\n\n"
                    else:
                        result += f"⚠️  Found {len(blocking_queries)} blocking situation(s):\n\n"
                        
                        # Group by blocking PID
                        blocking_groups = {}
                        for row in blocking_queries:
                            blocking_pid = row[0]
                            if blocking_pid not in blocking_groups:
                                blocking_groups[blocking_pid] = {
                                    'blocker': row[:7] + (row[13],),  # Include duration
                                    'blocked': []
                                }
                            blocking_groups[blocking_pid]['blocked'].append(
                                row[7:13] + (row[14],)  # Include duration
                            )
                        
                        # Display blocking chains
                        for idx, (blocking_pid, group) in enumerate(blocking_groups.items(), 1):
                            blocker = group['blocker']
                            blocked_list = group['blocked']
                            
                            result += f"🔴 Blocking Chain #{idx}\n"
                            result += "-" * 50 + "\n"
                            
                            # Blocker info
                            result += "BLOCKER:\n"
                            result += f"  • PID: {blocker[0]}\n"
                            result += f"  • User: {blocker[1]}\n"
                            result += f"  • Application: {blocker[2] or 'Unknown'}\n"
                            result += f"  • Client: {blocker[3] or 'Local'}\n"
                            result += f"  • Duration: {blocker[7]}\n"
                            result += f"  • State: {blocker[5]}\n"
                            result += f"  • Query: {blocker[6][:200]}{'...' if len(blocker[6]) > 200 else ''}\n\n"
                            
                            # Blocked queries
                            result += f"BLOCKED ({len(blocked_list)} queries):\n"
                            for blocked in blocked_list:
                                result += f"  → PID: {blocked[0]}\n"
                                result += f"    User: {blocked[1]}\n"
                                result += f"    App: {blocked[2] or 'Unknown'}\n"
                                result += f"    Duration: {blocked[6]}\n"
                                result += f"    Query: {blocked[5][:100]}{'...' if len(blocked[5]) > 100 else ''}\n\n"
                            
                            # Suggest resolution
                            result += "💡 RESOLUTION OPTIONS:\n"
                            result += f"  1. Cancel blocking query: SELECT pg_cancel_backend({blocking_pid});\n"
                            result += f"  2. Terminate blocking session: SELECT pg_terminate_backend({blocking_pid});\n"
                            result += "  3. Wait for blocking query to complete\n\n"
                    
                    # Get lock information if requested
                    if include_locks:
                        result += "🔐 LOCK INFORMATION\n"
                        result += "="*50 + "\n\n"
                        
                        # Get current locks
                        cur.execute("""
                            SELECT 
                                l.locktype,
                                l.database,
                                l.relation::regclass,
                                l.page,
                                l.tuple,
                                l.virtualxid,
                                l.transactionid,
                                l.classid,
                                l.objid,
                                l.objsubid,
                                l.virtualtransaction,
                                l.pid,
                                l.mode,
                                l.granted,
                                l.fastpath,
                                a.usename,
                                a.application_name,
                                a.client_addr,
                                a.query_start,
                                a.state,
                                a.query
                            FROM pg_locks l
                            JOIN pg_stat_activity a ON l.pid = a.pid
                            WHERE NOT l.granted
                            ORDER BY a.query_start
                        """)
                        
                        waiting_locks = cur.fetchall()
                        
                        if waiting_locks:
                            result += f"Found {len(waiting_locks)} processes waiting for locks:\n\n"
                            
                            for lock in waiting_locks[:10]:  # Limit display
                                locktype, database, relation, page, tuple, virtualxid, transactionid, \
                                classid, objid, objsubid, virtualtransaction, pid, mode, granted, \
                                fastpath, usename, app_name, client_addr, query_start, state, query = lock
                                
                                result += f"• PID {pid} waiting for {mode} lock on {locktype}\n"
                                if relation:
                                    result += f"  Table: {relation}\n"
                                result += f"  User: {usename}\n"
                                result += f"  Application: {app_name or 'Unknown'}\n"
                                result += f"  Query: {query[:100]}{'...' if query and len(query) > 100 else ''}\n\n"
                            
                            if len(waiting_locks) > 10:
                                result += f"... and {len(waiting_locks) - 10} more waiting locks\n\n"
                        else:
                            result += "No processes waiting for locks.\n\n"
                    
                    # Get long-running queries that might cause blocking
                    result += "⏱️  LONG-RUNNING QUERIES\n"
                    result += "="*50 + "\n\n"
                    
                    cur.execute("""
                        SELECT 
                            pid,
                            usename,
                            application_name,
                            client_addr,
                            query_start,
                            state,
                            (NOW() - query_start) AS duration,
                            wait_event_type,
                            wait_event,
                            query
                        FROM pg_stat_activity
                        WHERE state != 'idle'
                        AND query NOT LIKE '%pg_stat_activity%'
                        AND (NOW() - query_start) > interval '%s milliseconds'
                        ORDER BY query_start
                        LIMIT 10
                    """, (min_duration_ms,))
                    
                    long_queries = cur.fetchall()
                    
                    if long_queries:
                        result += f"Queries running longer than {min_duration_ms}ms:\n\n"
                        
                        for query in long_queries:
                            pid, user, app, client, start, state, duration, wait_type, wait_event, sql = query
                            
                            result += f"• PID {pid} - Duration: {duration}\n"
                            result += f"  User: {user} | App: {app or 'Unknown'}\n"
                            result += f"  State: {state}"
                            if wait_type:
                                result += f" | Waiting on: {wait_type}/{wait_event}"
                            result += f"\n  Query: {sql[:100]}{'...' if len(sql) > 100 else ''}\n\n"
                    else:
                        result += f"No queries running longer than {min_duration_ms}ms\n\n"
                    
                    # Best practices
                    result += "📚 BEST PRACTICES:\n"
                    result += "-" * 50 + "\n"
                    result += "• Keep transactions short and commit/rollback promptly\n"
                    result += "• Use NOWAIT or lock timeouts for non-critical operations\n"
                    result += "• Consider using advisory locks for application-level locking\n"
                    result += "• Monitor pg_stat_activity regularly\n"
                    result += "• Set statement_timeout for long-running queries\n"
                    result += "• Use SELECT FOR UPDATE SKIP LOCKED when appropriate\n"
                    
                    return [types.TextContent(type="text", text=result)]
                    
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error analyzing blocking queries: {str(e)}"
            )]
    @staticmethod
    async def handle_table_bloat_analysis(arguments: Dict[str, Any] | None) -> List[types.TextContent]:
        """Analyze table bloat and suggest maintenance actions."""
        
        # Default parameters
        arguments = arguments or {}
        schema = arguments.get("schema", "public")
        min_size_mb = arguments.get("min_size_mb", 10)  # Minimum table size to analyze
        bloat_threshold = arguments.get("bloat_threshold", 20)  # Percentage threshold
        
        try:
            # Use sync psycopg for better compatibility
            import psycopg
            
            # Get database URI from environment
            db_uri = os.environ.get("DATABASE_URI")
            if not db_uri:
                return [types.TextContent(
                    type="text",
                    text="Error: DATABASE_URI environment variable not set"
                )]
            
            with psycopg.connect(db_uri) as conn:
                with conn.cursor() as cur:
                    result = "🎈 TABLE BLOAT ANALYSIS\n" + "="*50 + "\n\n"
                    
                    # Get current database name
                    cur.execute("SELECT current_database()")
                    current_db = cur.fetchone()[0]
                    result += f"Database: {current_db}\n"
                    result += f"Schema: {schema}\n"
                    result += f"Min Table Size: {min_size_mb}MB\n"
                    result += f"Bloat Threshold: {bloat_threshold}%\n\n"
                    
                    # Calculate table bloat using pg_stats
                    # This is an estimation based on statistics
                    cur.execute("""
                        WITH constants AS (
                            SELECT current_setting('block_size')::numeric AS bs,
                                   23 AS hdr,
                                   8 AS ma
                        ),
                        no_stats AS (
                            SELECT table_schema, table_name, 
                                   n_live_tup::numeric as est_rows,
                                   pg_table_size(relid)::numeric as table_size
                            FROM information_schema.tables
                            LEFT OUTER JOIN pg_stat_user_tables
                                ON table_schema=schemaname
                                AND table_name=tablename
                            INNER JOIN pg_class
                                ON relid=oid
                            WHERE NOT EXISTS (
                                SELECT 1
                                FROM pg_stats
                                WHERE schemaname=table_schema
                                AND tablename=table_name
                            )
                            AND table_schema NOT IN ('pg_catalog', 'information_schema')
                            AND table_schema = %s
                        ),
                        null_headers AS (
                            SELECT
                                hdr+1+(count(*)::int/8) AS nullhdr,
                                SUM((1-null_frac)*avg_width) AS datawidth,
                                MAX(null_frac) AS maxfracsum,
                                schemaname,
                                tablename,
                                n_live_tup
                            FROM pg_stats s,
                                 (SELECT schemaname, tablename, n_live_tup 
                                  FROM pg_stat_user_tables
                                  WHERE schemaname = %s) AS s2
                            WHERE s.schemaname = s2.schemaname
                            AND s.tablename = s2.tablename
                            GROUP BY 1, 2, 3, 4, 5, 6
                        ),
                        data_headers AS (
                            SELECT
                                ma,
                                bs,
                                hdr,
                                schemaname,
                                tablename,
                                n_live_tup,
                                (datawidth+(hdr+ma-(CASE WHEN hdr%ma=0 THEN ma ELSE hdr%ma END)))::numeric AS datahdr,
                                (maxfracsum*(nullhdr+ma-(CASE WHEN nullhdr%ma=0 THEN ma ELSE nullhdr%ma END))) AS nullhdr2
                            FROM null_headers
                            CROSS JOIN constants
                        ),
                        table_estimates AS (
                            SELECT
                                schemaname,
                                tablename,
                                n_live_tup,
                                bs,
                                reltuples::numeric as est_rows,
                                relpages * bs as table_bytes,
                                CEIL((reltuples*
                                     ((datahdr+ma-(CASE WHEN datahdr%ma=0 THEN ma ELSE datahdr%ma END))+
                                      nullhdr2+4))/(bs-20::float)) * bs AS expected_bytes,
                                CASE WHEN relpages < 1 THEN 0
                                     ELSE (relpages * bs - CEIL((reltuples*
                                          ((datahdr+ma-(CASE WHEN datahdr%ma=0 THEN ma ELSE datahdr%ma END))+
                                           nullhdr2+4))/(bs-20::float)) * bs)::numeric
                                END AS bloat_bytes
                            FROM data_headers
                            JOIN pg_class ON tablename=relname AND schemaname=nspname
                            WHERE relkind='r'
                        ),
                        bloat_data AS (
                            SELECT
                                schemaname,
                                tablename,
                                n_live_tup,
                                table_bytes,
                                expected_bytes,
                                bloat_bytes,
                                CASE WHEN table_bytes > 0 
                                     THEN round(bloat_bytes*100/table_bytes,2)
                                     ELSE 0 
                                END AS bloat_pct,
                                CASE WHEN expected_bytes > 0 AND bloat_bytes > 0
                                     THEN round(bloat_bytes/(1024^2)::numeric,2)
                                     ELSE 0
                                END AS bloat_mb,
                                round(table_bytes/(1024^2)::numeric,2) AS table_mb,
                                round(expected_bytes/(1024^2)::numeric,2) AS expected_mb
                            FROM table_estimates
                            WHERE schemaname = %s
                            AND table_bytes >= (%s * 1024 * 1024)
                            ORDER BY bloat_bytes DESC
                        )
                        SELECT * FROM bloat_data
                        WHERE bloat_pct >= %s
                    """, (schema, schema, schema, min_size_mb, bloat_threshold))
                    
                    bloated_tables = cur.fetchall()
                    
                    if not bloated_tables:
                        result += f"✅ No tables found with bloat >= {bloat_threshold}% in schema '{schema}'\n\n"
                    else:
                        result += f"⚠️  Found {len(bloated_tables)} bloated tables:\n\n"
                        
                        total_bloat_mb = 0
                        total_table_mb = 0
                        
                        # Display bloated tables
                        for idx, (schemaname, tablename, n_live_tup, table_bytes, expected_bytes,
                                  bloat_bytes, bloat_pct, bloat_mb, table_mb, expected_mb) in enumerate(bloated_tables, 1):
                            
                            total_bloat_mb += float(bloat_mb)
                            total_table_mb += float(table_mb)
                            
                            result += f"{idx}. {schemaname}.{tablename}\n"
                            result += f"   • Table Size: {table_mb} MB\n"
                            result += f"   • Expected Size: {expected_mb} MB\n"
                            result += f"   • Bloat Size: {bloat_mb} MB ({bloat_pct}%)\n"
                            result += f"   • Live Tuples: {n_live_tup:,}\n"
                            
                            # Get additional statistics
                            cur.execute("""
                                SELECT 
                                    n_dead_tup,
                                    last_vacuum,
                                    last_autovacuum,
                                    vacuum_count,
                                    autovacuum_count,
                                    n_mod_since_analyze
                                FROM pg_stat_user_tables
                                WHERE schemaname = %s AND tablename = %s
                            """, (schemaname, tablename))
                            
                            stats = cur.fetchone()
                            if stats:
                                n_dead_tup, last_vacuum, last_autovacuum, vacuum_count, autovacuum_count, n_mod_since_analyze = stats
                                result += f"   • Dead Tuples: {n_dead_tup:,}\n"
                                if last_vacuum:
                                    result += f"   • Last Vacuum: {last_vacuum}\n"
                                if last_autovacuum:
                                    result += f"   • Last Autovacuum: {last_autovacuum}\n"
                            
                            # Suggest action based on bloat level
                            if bloat_pct > 50:
                                result += f"   🔴 CRITICAL: Consider VACUUM FULL or pg_repack\n"
                            elif bloat_pct > 30:
                                result += f"   🟡 WARNING: Schedule aggressive VACUUM\n"
                            else:
                                result += f"   🟢 MODERATE: Regular VACUUM should suffice\n"
                            
                            result += "\n"
                        
                        # Summary and recommendations
                        result += "📊 SUMMARY\n"
                        result += "="*50 + "\n"
                        result += f"Total Bloat: {total_bloat_mb:.2f} MB\n"
                        result += f"Total Table Size: {total_table_mb:.2f} MB\n"
                        result += f"Overall Bloat %: {(total_bloat_mb/total_table_mb*100):.1f}%\n\n"
                        
                        result += "🛠️ RECOMMENDED ACTIONS\n"
                        result += "="*50 + "\n"
                        
                        # Group tables by action needed
                        critical_tables = [t[1] for t in bloated_tables if float(t[6]) > 50]
                        warning_tables = [t[1] for t in bloated_tables if 30 < float(t[6]) <= 50]
                        moderate_tables = [t[1] for t in bloated_tables if float(t[6]) <= 30]
                        
                        if critical_tables:
                            result += "\n🔴 CRITICAL (>50% bloat) - Immediate action needed:\n"
                            for table in critical_tables:
                                result += f"\n-- Option 1: VACUUM FULL (locks table)\n"
                                result += f"VACUUM FULL {schema}.{table};\n"
                                result += f"\n-- Option 2: pg_repack (minimal locking)\n"
                                result += f"pg_repack -t {schema}.{table} -d {current_db}\n"
                        
                        if warning_tables:
                            result += "\n🟡 WARNING (30-50% bloat) - Schedule maintenance:\n"
                            for table in warning_tables:
                                result += f"VACUUM (VERBOSE, ANALYZE) {schema}.{table};\n"
                        
                        if moderate_tables:
                            result += "\n🟢 MODERATE (20-30% bloat) - Regular maintenance:\n"
                            for table in moderate_tables[:3]:  # Show first 3
                                result += f"VACUUM ANALYZE {schema}.{table};\n"
                            if len(moderate_tables) > 3:
                                result += f"... and {len(moderate_tables)-3} more tables\n"
                    
                    # Check autovacuum settings
                    result += "\n⚙️  AUTOVACUUM SETTINGS\n"
                    result += "="*50 + "\n"
                    
                    cur.execute("""
                        SELECT name, setting, unit, short_desc
                        FROM pg_settings
                        WHERE name LIKE 'autovacuum%'
                        ORDER BY name
                    """)
                    
                    autovac_settings = cur.fetchall()
                    for name, setting, unit, desc in autovac_settings:
                        result += f"• {name}: {setting}{' ' + unit if unit else ''}\n"
                    
                    # Best practices
                    result += "\n📚 BEST PRACTICES:\n"
                    result += "-" * 50 + "\n"
                    result += "• Monitor bloat regularly (weekly/monthly)\n"
                    result += "• Tune autovacuum to be more aggressive if needed\n"
                    result += "• Consider pg_repack for 24/7 systems\n"
                    result += "• Use FILLFACTOR < 100 for frequently updated tables\n"
                    result += "• Implement partitioning for very large tables\n"
                    result += "• Schedule VACUUM FULL during maintenance windows\n"
                    
                    return [types.TextContent(type="text", text=result)]
                    
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error analyzing table bloat: {str(e)}"
            )]