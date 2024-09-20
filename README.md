# **Capa**
- **Título do Projeto:** Contratos de Aluguéis Inteligentes usando Blockchain: Uma Solução para a Gestão Imobiliária
- **Nome do Estudante:** David Zimmermann Neto
- **Curso:** Engenharia de Software
- **Data de Entrega:** 02/12/2024

# **Resumo**
Neste trabalho é apresentada uma solução baseada em contratos inteligentes, utilizando a tecnologia blockchain, para a gestão de contratos de aluguel. O projeto busca melhorar a segurança, transparência e eficiência nos processos de locação, resolvendo problemas tais como falta de confiança entre as partes, processos burocráticos e rastreabilidade. Neste documento é contextualizado a tecnologia blockchain, justificando sua aplicação no setor imobiliário, os objetivos do projeto, e a descrição detalhada da solução proposta são apresenadas nas próximas seções.

# **1. Introdução**
## 1.1 Contexto
Com a digitalização crescente em diversas áreas, o setor imobiliário enfrenta desafios relacionados à segurança e à transparência nos processos de locação, bem como a rastreabilidade de documentos digitais. A tecnologia blockchain, com sua capacidade de oferecer registros imutáveis e seguros, surge como uma possível solução promissora para esses desafios.

## 1.2 Justificativa
A adoção de contratos inteligentes na engenharia de software, especificamente em contratos de aluguel, pode revolucionar a forma como acordos são gerenciados, reduzindo a burocracia e aumentando a confiança entre locadores e locatários. Este projeto é relevante para o campo da engenharia de software pois explora uma aplicação prática e inovadora da blockchain, um tema em ascensão.

## 1.3 Objetivos
- **Objetivo Principal:** Desenvolver uma plataforma de contratos de aluguel inteligente que utilize a tecnologia blockchain para garantir segurança, rastreabilidade e transparência.
- **Objetivos Secundários:**
  - Analisar as limitações e desafios da implementação de blockchain no setor imobiliário.
  - Avaliar a eficiência da solução proposta em comparação aos métodos tradicionais.
ACRESCENTAR OBJETIVOS ESPECÍFICOS

# **2. Descrição do Projeto**
## 2.1 Tema do Projeto
O projeto visa criar um sistema de contratos inteligentes, utilizando a tecnologia blockchain, para gerenciar contratos de aluguel. A solução proposta pretende automatizar a execução de contratos, assegurando que os termos acordados sejam cumpridos sem a necessidade de intermediários.

### 2.2 Problemas a Resolver
Os principais problemas a serem abordados são:

   - Reduzir a necessidade de intermediários e a burocracia associada à criação e gestão de contratos de aluguel.
   - Aumentar a transparência e a confiança entre locador e locatário ao garantir que os termos do contrato sejam imutáveis e executados conforme acordado.
   - Automatizar a execução dos termos do contrato, como pagamentos e notificações, para minimizar erros e disputas.
   - Proteger a integridade dos contratos e dados pessoais, evitando alterações não autorizadas e fraudes.

### 2.3 Limitações
É importante ressaltar as delimitações dos problemas que o projeto não abordará:

   - Não será adaptado para as leis de aluguel de diferentes países ou regiões.
   - Não haverá funcionalidades para a gestão de reparos, vistorias ou manutenção do imóvel.
   - Pagamentos fora do ambiente blockchain precisarão ser processados por plataformas externas.
   - A plataforma não substituirá a necessidade de validação por cartórios ou advogados especializados.
   - A interface e a documentação estarão disponíveis apenas em português brasileiro.
   - O projeto não incluirá versões para dispositivos móveis neste estágio.
   - Não haverá suporte para exportação de dados para análise externa ou relatórios fiscais.

## 3. Especificação Técnica

### 3.1 Requisitos de Software

#### 3.1.1 Lista de Requisitos
### Requisitos Funcionais (RF):
1. **Cadastrar Conta (RF1)**: O sistema deve permitir que locadores e locatários realizem o cadastro de suas contas.
2. **Realizar Login (RF2)**: O sistema deve permitir que os usuários façam login em suas contas.
3. **Autenticação (RF3)**: O sistema deve verificar as credenciais dos usuários com base em nome de usuário e senha.
4. **Criar Contrato Inteligente (RF4)**: O sistema deve permitir que locadores criem contratos de aluguel inteligentes, definindo termos como valor, duração e condições.
5. **Assinar Contrato (RF5)**: O sistema deve permitir que os locatários assinem digitalmente o contrato de aluguel na blockchain.
6. **Executar Contrato (RF6)**: O sistema deve garantir que os contratos sejam executados automaticamente, de acordo com os termos definidos (ex: pagamento do aluguel na data acordada).
7. **Registrar Pagamentos (RF7)**: O sistema deve registrar automaticamente os pagamentos realizados pelos locatários e vinculá-los ao contrato inteligente.
8. **Visualizar Histórico de Contratos (RF8)**: O sistema deve permitir que os usuários visualizem o histórico de contratos anteriores.
9. **Consultar Contratos em Andamento (RF9)**: O sistema deve fornecer uma funcionalidade que permita consultar os contratos de aluguel em andamento.
10. **Notificar Atrasos de Pagamento (RF10)**: O sistema deve notificar locadores e locatários em caso de atraso nos pagamentos automáticos.
11. **Encerrar Contrato (RF11)**: O sistema deve permitir que contratos sejam encerrados automaticamente ou por decisão mútua das partes envolvidas.
12. **Consulta de Disputas (RF12)**: O sistema deve permitir que os usuários consultem o status de disputas relacionadas a contratos.

### Requisitos Não-Funcionais (RNF):
1. **Segurança (RNF1)**: O sistema deve garantir um acesso seguro aos usuários, utilizando autenticação por dois fatores (2FA).
2. **Usabilidade (RNF2)**: O sistema deve ter uma interface amigável e intuitiva para facilitar o uso por locadores e locatários com pouco conhecimento técnico.
3. **Desempenho (RNF3)**: O sistema deve ser capaz de processar a criação e execução de contratos em até 5 segundos.
4. **Escalabilidade (RNF4)**: O sistema deve ser escalável para suportar um grande número de contratos simultâneos, mantendo o desempenho.
5. **Imutabilidade dos Contratos (RNF5)**: O sistema deve garantir a imutabilidade dos contratos armazenados na blockchain.
6. **Linguagens de Programação (RNF6)**: O sistema deve ser desenvolvido utilizando:
   - **Solidity** para os contratos inteligentes na blockchain Ethereum.
   - **Python** para análise e monitoramento de dados dos contratos.
7. **Banco de Dados (RNF7)**: O sistema deve utilizar o MongoDB/PostgreSQL para armazenar dados auxiliares como perfis de usuários e registros de atividades, além da blockchain para contratos.
8. **Conformidade Legal (RNF8)**: O sistema deve ser desenvolvido de acordo com as leis de proteção de dados e regulação de contratos de cada jurisdição.


#### 3.1.2 Representação dos Requisitos (A SER DESENVOLVIDO)
- Diagrama de Casos de Uso (UML) 

### 3.2 Considerações de Design (A SER DESENVOLVIDO)
#### 3.2.1 Visão Inicial da Arquitetura
![Design de Arquitetura](https://github.com/user-attachments/assets/7fdd2542-0c0f-4382-a1c4-2debe4612350)

O sistema será composto por estes componentes principais:
- **Interface do Cliente:** Plataforma web para interação com os contratos.
- **Aplicação Backend Django:** Processa as requisições e gerencia a lógica de negócios dos contratos.
- **API de Integração com Blockchain:** Faz a integração entre Backend e a Blockchain.
- **Blockchain Ethereum:** Onde os contratos inteligentes são implantados e executados.
- **Banco de Dados PostgreSQL/MongoDB:** Armazena dados auxiliares e relacionados aos contratos.

#### 3.2.2 Padrões de Arquitetura (A SER DESENVOLVIDO)

#### 3.2.3 Modelos C4 (A SER DESENVOLVIDO)

### 3.3 Stack Tecnológica

#### 3.3.1 Linguagens de Programação
- **Solidity:** Para a criação dos contratos inteligentes.
- **Python:** Para lógica backend e automação de processos.

#### 3.3.2 Frameworks e Bibliotecas
- **Flask/Django:** Para a lógica backend do sistema.
- **Ethereum:** Sistema blockchain utilizado

#### 3.3.3 Ferramentas de Desenvolvimento e Gestão de Projeto
- **Github:** Para controle de versão e gerenciamento de projeto.
- **Trello:** Para acompanhamento das tarefas e cronograma.
- **SonarQube:** Para testes unitários
- **Visual Studio Code:**
- **Wiki do Github:**
- **TDD:**
- **MongoDB/PostgreSQL:**

### 3.4 Considerações de Segurança (A SER DESENVOLVIDO)

## 4. Próximos Passos
O projeto continua em desenvolvimento, conforme a lista abaixo é apresentado os próximos passos: 

- [x] Aprovação dos professores 
  - [x] Receber feedback e melhorias 
  - [x] Registrar nota do RFC 
- [x] Apresentação - Defesa do Portfólio I 
- [x] Definição do plano de entregas 
- [ ] Receber aprovação do plano do produto 
- [ ] Publicar a definição das entregas no Trello
- [ ] Desenvolvimento do projeto 
- [ ] Apresentação Final – Defesa do Portfólio II 

## Plano de Entregas:

- [ ] Implementar smart contracts no Ethereum **(31/08/2024)**
  - [x] Definir termos do contrato inteligente
  - [x] Implementar e testar contratos
  - [ ] Validar a execução automática dos contratos
  - [ ] Disponibilizar os contratos na blockchain
- [ ] Implementar branch `dev` no GitHub **(31/08/2024)**
- [ ] Configurar SonarQube para análise de código **(07/09/2024)**
- [ ] Desenvolver a aplicação para gerenciamento dos contratos **(07/09/2024)**
  - [ ] Interface para criação de contratos
  - [ ] Assinatura digital via blockchain
  - [ ] Validação de pagamentos e notificações
- [ ] Aplicar testes E2E para toda a execução de contratos **(09/11/2024)**
- [ ] Implementar CI/CD para automatizar deploys e testes **(09/11/2024)**
- [ ] Finalizar e disponibilizar a Aplicação Web **(09/11/2024)**
  - [ ] Design principal das telas **(14/09/2024)**
    - [ ] Tela de Login
    - [ ] Tela de Cadastro
    - [ ] Painel de Controle dos Contratos
    - [ ] Histórico de Contratos
    - [ ] Status de Pagamentos
  - [ ] Definir mockup para testes iniciais **(21/09/2024)**
  - [ ] Desenvolver as telas principais **(09/11/2024)**
- [ ] Aplicar integrações com blockchain e banco de dados **(16/11/2024)**
- [ ] Revisar segurança dos contratos e proteção de dados **(16/11/2024)**
- [ ] Revisar cobertura de testes E2E **(16/11/2024)**
- [ ] Revisar pipeline CI/CD **(16/11/2024)**
- [ ] Disponibilizar a aplicação em ambiente Cloud **(18/11/2024)**

## 5. Referências

1. **Ethereum**: Plataforma blockchain utilizada para a criação e execução de contratos inteligentes. O Ethereum permite a descentralização e a automação de contratos sem a necessidade de intermediários.
   - Site: [https://ethereum.org/](https://ethereum.org/)

2. **Solidity**: Linguagem de programação usada para implementar contratos inteligentes na plataforma Ethereum. O Solidity é a principal linguagem para o desenvolvimento de contratos inteligentes e oferece um alto nível de abstração para manipular dados na blockchain.
   - Documentação: [https://docs.soliditylang.org/](https://docs.soliditylang.org/)

3. **Ganache**: Ferramenta que cria um blockchain local para desenvolvimento e testes de contratos inteligentes. Usado para simular a rede Ethereum e testar contratos antes de serem implantados na mainnet.
   - Documentação: [https://trufflesuite.com/ganache/](https://trufflesuite.com/ganache/)

4. **Truffle**: Framework para desenvolvimento de contratos inteligentes com suporte para compilação, migração e testes. Truffle simplifica o processo de gerenciamento do ciclo de vida dos contratos.
   - Documentação: [https://trufflesuite.com/](https://trufflesuite.com/)

5. **Metamask**: Extensão de navegador que permite aos usuários interagirem com a blockchain Ethereum diretamente do navegador, facilitando o acesso a contratos inteligentes e a assinatura de transações.
   - Site: [https://metamask.io/](https://metamask.io/)

6. **SonarQube**: Ferramenta para análise contínua da qualidade do código. Usado para garantir que o código desenvolvido atenda aos padrões de segurança, desempenho e manutenibilidade.
   - Documentação: [https://www.sonarqube.org/](https://www.sonarqube.org/)

7. **GitHub**: Plataforma de hospedagem de código que facilita a colaboração no desenvolvimento de software. O GitHub será utilizado para controle de versão e integração contínua (CI/CD) do projeto.
   - Site: [https://github.com/](https://github.com/)

8. **Docker**: Ferramenta que permite a criação e gerenciamento de contêineres, facilitando o deploy e a portabilidade da aplicação entre diferentes ambientes. **(A SER REVISTO)**
   - Documentação: [https://docs.docker.com/](https://docs.docker.com/)

9. **CircleCI**: Ferramenta de integração e entrega contínua (CI/CD) que automatiza o build, testes e deploy do projeto em ambientes de produção. **(A SER REVISTO)**
   - Documentação: [https://circleci.com/](https://circleci.com/)

11. **MongoDB**: Banco de dados NoSQL que será utilizado para armazenar informações relacionadas aos contratos e transações, facilitando a consulta rápida e o gerenciamento eficiente dos dados. **(A SER AVALIADO JUNTAMENTE COM O POSTGRESQL)**
    - Documentação: [https://www.mongodb.com/](https://www.mongodb.com/)

12. **Postman**: Ferramenta de teste de API que permite realizar consultas e interações com APIs para validar o comportamento dos contratos inteligentes no backend.
    - Site: [https://www.postman.com/](https://www.postman.com/)


## 6. Apêndices (Opcionais)
- Anexos com exemplos de contratos inteligentes.
- Código fonte detalhado dos principais componentes do sistema.
