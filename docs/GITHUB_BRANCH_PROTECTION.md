# GitHub Branch Protection - Implementação

**Versão:** 1.0  
**Data:** Fevereiro 2026  
**Status:** 📋 Guia de Implementação

---

## 📋 Visão Geral

Este documento descreve como configurar **GitHub Branch Protection Rules** para o repositório VokeTag, garantindo qualidade de código, segurança e conformidade com práticas enterprise.

---

## 🎯 Objetivos

- ✅ Prevenir commits diretos na branch `main`
- ✅ Exigir revisão de código (Pull Request obrigatório)
- ✅ Garantir que CI/CD checks passem antes do merge
- ✅ Manter histórico linear e auditável
- ✅ Implementar CODEOWNERS review automático

---

## 🔧 Configuração Recomendada

### Branch: `main` (Production)

#### 1. Require Pull Request Reviews

**Configuração:**
```
Settings → Branches → Branch protection rules → Add rule
```

**Pattern:** `main`

**Opções Obrigatórias:**

- ☑ **Require a pull request before merging**
  - ☑ **Require approvals:** `1` (mínimo)
  - ☑ **Dismiss stale pull request approvals when new commits are pushed**
  - ☑ **Require review from Code Owners** (usa `.github/CODEOWNERS`)
  - ☐ **Restrict who can dismiss pull request reviews** (opcional - somente tech leads)

**Justificativa:**
- Garante que todo código seja revisado por pelo menos 1 pessoa
- CODEOWNERS automaticamente solicitam review dos responsáveis
- Novas alterações invalidam approvals anteriores (prevent "silent changes")

---

#### 2. Require Status Checks

**Opções Obrigatórias:**

- ☑ **Require status checks to pass before merging**
  - ☑ **Require branches to be up to date before merging**
  
**Status Checks Necessários:**
```
✓ CI / Lint Factory Service (Python)
✓ CI / Lint Scan Service (Go)
✓ CI / Unit Tests Factory
✓ CI / Unit Tests Scan
✓ CI / Unit Tests Blockchain
✓ CI / Unit Tests Admin
✓ CI / Docker Build (all services)
✓ Security / Trivy Scan
✓ Security / Dependency Audit
```

**Justificativa:**
- Garante que testes passem antes de merge
- Previne breaking changes
- Security scans devem passar (Trivy para vulnerabilidades)

---

#### 3. Require Signed Commits (Opcional - Recomendado)

**Opções:**

- ☑ **Require signed commits**
  - Exige GPG/SSH signature em todos os commits
  - Aumenta auditoria e non-repudiation

**Setup para desenvolvedores:**
```bash
# Configurar GPG signing
git config --global user.signingkey YOUR_GPG_KEY_ID
git config --global commit.gpgsign true

# Ou SSH signing (GitHub suporta desde 2022)
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
```

**Justificativa:**
- Compliance SOC2/ISO27001
- Garante identidade do autor
- Previne commits maliciosos

---

#### 4. Require Linear History

**Opções:**

- ☑ **Require linear history**
  - ☐ **Allow merge commits** (desabilitar)
  - ☑ **Allow squash merging** (habilitar)
  - ☐ **Allow rebase merging** (desabilitar)

**Justificativa:**
- Histórico limpo e rastreável
- Facilita git bisect e rollbacks
- Padrão enterprise

---

#### 5. Additional Restrictions

**Opções Recomendadas:**

- ☑ **Do not allow bypassing the above settings**
  - Nem admins podem bypass (except emergency)
  
- ☑ **Restrict who can push to matching branches**
  - Somente: `@technical-lead`, `@devops-team`, `@github-actions[bot]`
  
- ☑ **Require deployments to succeed before merging** (opcional)
  - Exige deploy em staging antes de production

- ☑ **Lock branch** (opcional - para frozen releases)
  - Previne qualquer mudança temporariamente

**Justificativa:**
- Zero tolerance para bypass (except emergency override)
- Apenas CI/CD e tech leads podem merge
- Deploy automático garante staging validação

---

### Branch: `develop` (Development)

**Configuração mais flexível:**

```
Settings → Branches → Branch protection rules → Add rule
```

**Pattern:** `develop`

**Opções:**

- ☑ **Require a pull request before merging**
  - ☑ **Require approvals:** `1`
  - ☐ Dismiss stale reviews (não necessário em dev)
  - ☐ Require Code Owners review (opcional)

- ☑ **Require status checks to pass before merging**
  - ☑ Branches up to date
  - Status checks: Same as `main` (CI, tests, security)

- ☐ **Require linear history** (permite merge commits em dev)

**Justificativa:**
- Desenvolvimento mais ágil
- Ainda exige review + CI
- Permite experimentação

---

### Branch: `release/*` (Release Candidates)

**Pattern:** `release/*`

**Configuração:**

- ☑ Same as `main` (strict protection)
- ☑ **Require linear history**
- ☑ **Require signed commits**
- ☑ **Lock branch** após release (prevent hotfixes in wrong branch)

**Justificativa:**
- Release branches são tão críticas quanto main
- Devem ser immutable após deploy

---

## 🚀 Implementação Passo a Passo

### 1. Acessar GitHub Settings

```
GitHub.com → voketag/voketag repository
→ Settings (tab)
→ Branches (left sidebar)
→ Branch protection rules
→ Add rule
```

### 2. Configurar `main` Branch

```yaml
# Branch name pattern
main

# Protect matching branches
☑ Require a pull request before merging
  ☑ Require 1 approval
  ☑ Dismiss stale approvals
  ☑ Require review from Code Owners

☑ Require status checks to pass before merging
  ☑ Require branches to be up to date
  Status checks:
    - CI / Lint Factory Service (Python)
    - CI / Lint Scan Service (Go)
    - CI / Unit Tests Factory
    - CI / Unit Tests Scan
    - CI / Docker Build (all services)
    - Security / Trivy Scan

☑ Require linear history

☑ Do not allow bypassing the above settings

☑ Restrict who can push to matching branches
  - @technical-lead
  - @devops-team
  - github-actions[bot]

☐ Allow force pushes (NEVER enable)
☐ Allow deletions (NEVER enable)
```

**👉 Click "Create" ou "Save changes"**

### 3. Configurar `develop` Branch

```yaml
# Branch name pattern
develop

# Protect matching branches
☑ Require a pull request before merging
  ☑ Require 1 approval
  ☐ Dismiss stale approvals
  ☐ Require review from Code Owners

☑ Require status checks to pass before merging
  ☑ Require branches to be up to date
  Status checks: [same as main]

☐ Require linear history
☑ Do not allow bypassing the above settings

☐ Restrict who can push (mais permissivo)

☐ Allow force pushes (NEVER)
☐ Allow deletions (NEVER)
```

### 4. Configurar `release/*` Branches

```yaml
# Branch name pattern
release/*

# Same settings as main (strict protection)
```

---

## 🔍 Validação

### Testar Branch Protection

**1. Tentar commit direto no main (deve falhar):**

```bash
git checkout main
echo "test" > test.txt
git add test.txt
git commit -m "test"
git push origin main
```

**Resultado esperado:**
```
remote: error: GH006: Protected branch update failed for refs/heads/main.
remote: error: At least 1 approving review is required by reviewers with write access.
To https://github.com/voketag/voketag.git
 ! [remote rejected] main -> main (protected branch hook declined)
```

✅ **SUCESSO** - Branch protection está funcionando!

**2. Criar Pull Request (deve funcionar):**

```bash
git checkout -b feature/test-branch-protection
echo "test" > test.txt
git add test.txt
git commit -m "test: validate branch protection"
git push origin feature/test-branch-protection
```

**No GitHub:**
- Open Pull Request para `main`
- Verificar que status checks estão rodando
- Verificar que "Merge" está bloqueado até review + CI passar
- Solicitar review de Code Owner automaticamente

✅ **SUCESSO** - Pull Request workflow funcionando!

---

## 📋 Checklist de Implementação

### Pré-requisitos

- [x] `.github/CODEOWNERS` criado
- [x] CI/CD workflows configurados (`.github/workflows/ci.yml`)
- [x] Security scans configurados (Trivy, dependency audit)
- [ ] GitHub repository settings → Settings → General → Allow merge commits (disabled)
- [ ] GitHub repository settings → Settings → General → Allow squash merging (enabled)
- [ ] GitHub repository settings → Settings → General → Allow rebase merging (disabled)

### Implementação

**Branch: `main`**
- [ ] Require pull request reviews (1 approval)
- [ ] Require Code Owners review
- [ ] Dismiss stale approvals
- [ ] Require status checks (all CI jobs)
- [ ] Require branches up to date
- [ ] Require linear history
- [ ] Restrict push access (tech leads + CI/CD only)
- [ ] Do not allow bypass
- [ ] No force pushes
- [ ] No deletions

**Branch: `develop`**
- [ ] Require pull request reviews (1 approval)
- [ ] Require status checks
- [ ] No force pushes

**Branch: `release/*`**
- [ ] Same as `main` (strict)

### Validação

- [ ] Teste commit direto (deve falhar)
- [ ] Teste Pull Request (deve funcionar)
- [ ] Teste merge sem review (deve falhar)
- [ ] Teste merge sem CI passing (deve falhar)
- [ ] Teste merge com review + CI (deve funcionar)

---

## 🚨 Emergency Override

### Quando Usar

**Somente em situações críticas:**
- Incident P0 (production down)
- Security vulnerability crítico (hotfix urgente)
- Data loss prevention

### Como Fazer

1. Tech Lead ou Admin deve:
   - Temporariamente desabilitar branch protection
   - Fazer commit direto ou force push
   - **RE-HABILITAR branch protection imediatamente**
   - Abrir post-mortem issue

2. Documentar no post-mortem:
   - Motivo do bypass
   - Timestamp
   - Commits afetados
   - Root cause

---

## 🎯 Benefícios

### Qualidade de Código

✅ **Code review obrigatório** (minimum 1 person)  
✅ **CODEOWNERS review** (domain experts approve)  
✅ **CI/CD validation** (tests, linting, security)  
✅ **Linear history** (easy rollback)

### Segurança

✅ **Prevent malicious commits** (review required)  
✅ **Security scans** (Trivy, dependency audit)  
✅ **Signed commits** (auditability)  
✅ **No direct pushes** (zero bypass tolerance)

### Compliance

✅ **SOC2 compliant** (change management)  
✅ **ISO27001 compliant** (access control)  
✅ **Audit trail** (all changes via PR)  
✅ **Segregation of duties** (Code Owners)

---

## 📚 Referências

- [GitHub Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [GitHub Signed Commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification)
- [VokeTag CODEOWNERS](../.github/CODEOWNERS)
- [VokeTag CI/CD Workflows](../.github/workflows/)

---

## 👥 Ownership

**DRI (Directly Responsible Individual):** `@devops-team`  
**Reviewers:** `@technical-lead`, `@security-team`  
**Enforcement:** GitHub Branch Protection Rules (automated)

---

**Status:** ✅ Pronto para implementação  
**Última atualização:** Fevereiro 23, 2026  
**Próxima revisão:** Maio 2026 (pós Sprint 2)
