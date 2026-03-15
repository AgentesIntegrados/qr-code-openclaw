'use client';

import { useState } from "react";
import { ProtectedRoute } from '@/components/protected-route';
import { SelecaoInstanciasComponent } from "@/components/selecao-instancias";
import { EntradaContatosComponent } from "@/components/entrada-contatos";
import { ComposicaoMensagemComponent } from "@/components/composicao-mensagem";
import type { Contact, Instance } from "@/types";

type Step = 'selecao' | 'contatos' | 'composicao';

export default function Page() {
  const [currentStep, setCurrentStep] = useState<Step>('selecao');
  const [selectedInstances, setSelectedInstances] = useState<Instance[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);

  const handleSelecaoInstancias = (instances: Instance[]) => {
    setSelectedInstances(instances);
    setCurrentStep('contatos');
  };

  const handleEntradaContatos = (contactsData: Contact[]) => {
    setContacts(contactsData);
    setCurrentStep('composicao');
  };

  return (
    <ProtectedRoute>
      {(() => {
        switch (currentStep) {
          case 'selecao':
            return <SelecaoInstanciasComponent onNextStep={handleSelecaoInstancias} />;
          case 'contatos':
            return (
              <EntradaContatosComponent 
                selectedInstances={selectedInstances}
                onNextStep={handleEntradaContatos}
              />
            );
          case 'composicao':
            return (
              <ComposicaoMensagemComponent 
                selectedInstances={selectedInstances}
                contacts={contacts}
              />
            );
          default:
            return <SelecaoInstanciasComponent onNextStep={handleSelecaoInstancias} />;
        }
      })()}
    </ProtectedRoute>
  );
}