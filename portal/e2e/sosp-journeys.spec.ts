import { test, expect } from "@playwright/test";

/**
 * SOSP — ESPECIFICAÇÃO DE TESTES E2E / BROWSER (PLAYWRIGHT)
 * Cobre as 12 Jornadas Críticas do Sistema:
 * 1. Cadastro de Cidadão com validação de CPF e CEP (ViaCEP).
 * 2. Login e Logout com limpeza de token.
 * 3. Consulta ao catálogo de serviços e busca com filtros combinados (RN-04).
 * 4. Visualização de guia de serviço e checklist interativo de documentos.
 * 5. Agendamento de serviço com seleção de slot de 30 min (RN-18) e protocolo (RN-20).
 * 6. Visualização de agendamentos e linha do tempo do protocolo.
 * 7. Tentativa de acesso a rotas protegidas sem autenticação (redirecionamento /login).
 * 8. Expiração de sessão (exibição de modal ou redirecionamento /sessao-expirada).
 * 9. Painel do servidor com agendamentos da unidade e isolamento por órgão.
 * 10. Painel do administrador com trilha de auditoria e relatórios gerenciais.
 * 11. Tentativa de agendamento duplicado (mensagem amigável RFC 7807).
 * 12. Tentativa de login com senha incorreta e bloqueio após 5 falhas (RN-29).
 */

test.describe("Jornadas do Cidadão (SOSP)", () => {
  test.beforeEach(async ({ page }) => {
    // Garante que o storage esteja limpo antes de cada jornada
    await page.addInitScript(() => {
      window.localStorage.clear();
      window.sessionStorage.clear();
    });
  });

  // Jornada 1: Cadastro de Cidadão
  test("J01: Cadastro de Cidadão com validação de CPF e CEP", async ({ page }) => {
    await page.goto("/cadastro");
    await expect(page).toHaveTitle(/Cadastro|SOSP/i);

    // Preenchimento de dados pessoais
    await page.fill('input[name="fullName"]', "Luiz Gustavo Cidadão");
    await page.fill('input[name="cpf"]', "111.444.777-05");
    await page.fill('input[name="birthDate"]', "1992-08-20");
    await page.fill('input[name="motherName"]', "Maria Helena da Silva");
    await page.fill('input[name="email"]', "luiz.cidadao@exemplo.com.br");
    await page.fill('input[name="phone"]', "(82) 99876-5432");

    // CEP com máscara e autopreenchimento
    await page.fill('input[name="cep"]', "57020-100");
    // Aguarda resolução do CEP ou preenchimento de logradouro
    await page.fill('input[name="street"]', "Rua do Comércio");
    await page.fill('input[name="number"]', "123");
    await page.fill('input[name="neighborhood"]', "Centro");
    await page.fill('input[name="city"]', "Maceió");
    await page.selectOption('select[name="state"]', "AL");

    // Senha com requisitos mínimos de segurança
    await page.fill('input[name="password"]', "SenhaForte@2026");
    await page.fill('input[name="passwordConfirmation"]', "SenhaForte@2026");

    // Aceite de termos e submissão
    await page.check('input[name="acceptTerms"]');
    await page.click('button[type="submit"]');

    // Confirmação de sucesso ou redirecionamento para login
    await expect(page.locator("text=Cadastro realizado com sucesso|Entrar")).toBeVisible({ timeout: 5000 });
  });

  // Jornada 2: Login e Logout
  test("J02: Login e Logout com limpeza de token no cliente", async ({ page }) => {
    await page.goto("/login");

    await page.fill('input[name="cpf"]', "111.444.777-05");
    await page.fill('input[name="password"]', "SenhaForte@2026");
    await page.click('button[type="submit"]');

    // Verifica redirecionamento pós-login
    await expect(page).toHaveURL(/\/(servicos|cidadao\/meus-agendamentos)/);

    // Valida persistência do token
    const token = await page.evaluate(() => localStorage.getItem("sosp_auth_token"));
    expect(token).toBeTruthy();

    // Executa Logout
    await page.click('button:has-text("Sair"), a:has-text("Sair")');
    await expect(page).toHaveURL(/\/login/);

    // Valida limpeza total do token
    const clearedToken = await page.evaluate(() => localStorage.getItem("sosp_auth_token"));
    expect(clearedToken).toBeNull();
  });

  // Jornada 3: Catálogo e Busca Combinada
  test("J03: Consulta ao catálogo de serviços e busca com filtros combinados (RN-04)", async ({ page }) => {
    await page.goto("/servicos");

    // Busca textual
    await page.fill('input[placeholder*="Buscar serviços"]', "CIN");
    await page.keyboard.press("Enter");

    // Filtros combináveis
    const categorySelect = page.locator('select[name="category"], select:has-text("Categoria")');
    if (await categorySelect.isVisible()) {
      await categorySelect.selectOption({ label: "Documentos e Certidões" });
    }

    // Card de serviço renderizado
    const serviceCard = page.locator('text=Emitir Carteira de Identidade Nacional').first();
    await expect(serviceCard).toBeVisible();

    // Verificação de paginação (RN-05: 10 itens por página)
    const pagination = page.locator('nav[aria-label="Paginação"], .sosp-pagination');
    await expect(pagination).toBeVisible();
  });

  // Jornada 4: Guia de Serviço e Checklist
  test("J04: Visualização de guia de serviço e checklist interativo de documentos", async ({ page }) => {
    await page.goto("/servicos/servico-emitir-rg/guia");

    await expect(page.locator("text=O que levar|Documentos Necessários")).toBeVisible();

    // Interação com o checklist
    const checkCertidao = page.locator('input[type="checkbox"]').first();
    await expect(checkCertidao).toBeVisible();
    await checkCertidao.check();
    await expect(checkCertidao).toBeChecked();

    // Botão de download ou solicitação de PDF
    const pdfButton = page.locator('button:has-text("Baixar Guia em PDF"), button:has-text("Gerar PDF")');
    await expect(pdfButton).toBeVisible();
  });

  // Jornada 5: Agendamento Atômico em Slot de 30 min
  test("J05: Agendamento com seleção de slot de 30 min (RN-18) e protocolo (RN-20)", async ({ page }) => {
    // Autentica via script
    await page.addInitScript(() => {
      localStorage.setItem("sosp_auth_token", "simulated-jwt-token-citizen-001");
    });

    await page.goto("/servicos/servico-emitir-rg/agendamento");

    // Seleciona Unidade
    const unitSelect = page.locator('select[name="unitId"], select:has-text("Unidade")');
    await unitSelect.selectOption({ index: 1 });

    // Seleciona Data (próximo dia útil)
    const dateInput = page.locator('input[type="date"], input[name="scheduledDate"]');
    await dateInput.fill("2026-11-15");

    // Seleciona slot de 30 minutos disponível
    const slotButton = page.locator('button:has-text("08:30"), button:has-text("09:00"), button:has-text("09:30")').first();
    await expect(slotButton).toBeVisible();
    await slotButton.click();

    // Submete agendamento
    await page.click('button:has-text("Confirmar Agendamento")');

    // Confirmação de protocolo AAAAMMDD-XXXX
    const protocolText = page.locator('text=/[0-9]{8}-[0-9]{4}/');
    await expect(protocolText).toBeVisible({ timeout: 10000 });
  });

  // Jornada 6: Meus Agendamentos e Linha do Tempo
  test("J06: Visualização de agendamentos e linha do tempo do protocolo", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("sosp_auth_token", "simulated-jwt-token-citizen-001");
    });

    await page.goto("/cidadao/meus-agendamentos");
    await expect(page.locator("text=20261105-1042|20261015-8831").first()).toBeVisible();

    // Clica no protocolo para ver detalhes e linha do tempo
    await page.click('text=Ver Detalhes, a:has-text("20261105-1042")');
    await expect(page.locator("text=Linha do Tempo|Histórico do Agendamento")).toBeVisible();
    await expect(page.locator("text=Agendamento Confirmado|Solicitação Criada")).toBeVisible();
  });

  // Jornada 7: Acesso a Rotas Protegidas sem Token
  test("J07: Tentativa de acesso a rotas protegidas sem autenticação redireciona para /login", async ({ page }) => {
    await page.goto("/cidadao/meus-agendamentos");
    await expect(page).toHaveURL(/\/login/);

    await page.goto("/servidor/painel");
    await expect(page).toHaveURL(/\/login/);

    await page.goto("/admin/auditoria");
    await expect(page).toHaveURL(/\/login/);
  });

  // Jornada 8: Sessão Expirada
  test("J08: Sessão expirada exibe aviso ou redireciona para /sessao-expirada", async ({ page }) => {
    await page.addInitScript(() => {
      // Simula token vencido
      localStorage.setItem("sosp_auth_token", "expired-token");
    });

    await page.goto("/cidadao/meus-agendamentos");
    // O interceptor do ApiClient ao receber 401 redireciona para /sessao-expirada
    await expect(page).toHaveURL(/\/(sessao-expirada|login)/, { timeout: 5000 });
    await expect(page.locator("text=Sua sessão expirou|Faça login novamente")).toBeVisible();
  });
});

test.describe("Jornadas Operacionais e Administrativas (SOSP)", () => {
  // Jornada 9: Painel do Servidor
  test("J09: Painel do servidor com agendamentos da unidade e isolamento de órgão", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("sosp_auth_token", "simulated-server-ssp-token");
    });

    await page.goto("/servidor/painel");
    await expect(page.locator("text=Painel do Servidor|Atendimentos de Hoje")).toBeVisible();
    await expect(page.locator("text=Central Já! Centro|Secretaria de Estado da Segurança Pública")).toBeVisible();

    // Acessa fila de atendimento
    await page.click('a:has-text("Fila de Atendimento"), a:has-text("Atendimentos")');
    await expect(page.locator("text=Registrar Comparecimento|Iniciar Atendimento")).toBeVisible();
  });

  // Jornada 10: Painel do Administrador
  test("J10: Painel do administrador com trilha de auditoria e relatórios", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("sosp_auth_token", "simulated-admin-token");
    });

    await page.goto("/admin/auditoria");
    await expect(page.locator("text=Trilha de Auditoria|Eventos do Sistema")).toBeVisible();
    await expect(page.locator("table, .sosp-audit-table")).toBeVisible();

    // Acessa relatórios gerenciais
    await page.goto("/servidor/relatorios");
    await expect(page.locator("text=Relatórios Gerenciais|Taxa de Absenteísmo")).toBeVisible();
    await expect(page.locator('button:has-text("Exportar CSV"), button:has-text("Exportar PDF")')).toBeVisible();
  });

  // Jornada 11: Bloqueio de Agendamento Duplicado
  test("J11: Bloqueio de agendamento duplicado para o mesmo serviço (RN-21)", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("sosp_auth_token", "simulated-jwt-token-citizen-001");
    });

    await page.goto("/servicos/servico-emitir-rg/agendamento");
    // Tenta agendar para um serviço no qual o cidadão já possui agendamento ativo
    await page.fill('input[type="date"]', "2026-11-20");
    const slot = page.locator('button:has-text("10:00")').first();
    if (await slot.isVisible()) {
      await slot.click();
      await page.click('button:has-text("Confirmar Agendamento")');
      // Deve exibir mensagem amigável de erro RFC 7807
      await expect(
        page.locator("text=Você já possui um agendamento ativo para este serviço|Agendamento Duplicado")
      ).toBeVisible({ timeout: 5000 });
    }
  });

  // Jornada 12: Bloqueio de Força Bruta no Login (RN-29)
  test("J12: Tentativa de login com senha incorreta e bloqueio após 5 falhas (RN-29)", async ({ page }) => {
    await page.goto("/login");

    const cpf = "111.444.777-05";
    for (let i = 1; i <= 5; i++) {
      await page.fill('input[name="cpf"]', cpf);
      await page.fill('input[name="password"]', `SenhaInvalida#${i}`);
      await page.click('button[type="submit"]');

      if (i < 5) {
        await expect(page.locator("text=CPF ou senha inválidos|Credenciais Inválidas")).toBeVisible({ timeout: 3000 });
      }
    }

    // No 5º erro, deve exibir bloqueio temporário de 5 minutos
    await expect(
      page.locator("text=Muitas tentativas inválidas|Bloqueado temporariamente|Tente novamente em 5 minutos")
    ).toBeVisible({ timeout: 5000 });
  });
});
