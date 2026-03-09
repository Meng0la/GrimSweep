import os
import shutil
import subprocess
import sys
import ctypes
import time
import glob
from pathlib import Path

# ==============================================
# VERIFICAÇÃO DE ADMINISTRADOR
# ==============================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ==============================================
# UTILITÁRIOS
# ==============================================
def run_cmd(command, capture=True):
    """Executa um comando no shell e retorna a saída."""
    try:
        result = subprocess.run(command, shell=True, capture_output=capture, text=True)
        return result.stdout if capture else None
    except Exception as e:
        print(f"Erro ao executar comando: {command}\n{e}")
        return ""

def run_powershell(command):
    """Executa um comando PowerShell."""
    return run_cmd(f'powershell -Command "{command}"')

def delete_path(path, description):
    """Apaga um arquivo ou pasta, com mensagem de erro amigável."""
    if not os.path.exists(path):
        print(f"⚠ Caminho não encontrado: {description}")
        return
    try:
        if os.path.isfile(path):
            os.remove(path)
            print(f"✔ Arquivo removido: {description}")
        elif os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
            print(f"✔ Pasta removida: {description}")
    except Exception as e:
        print(f"✘ Erro ao remover {description}: {e}")

def delete_contents(folder, description):
    """Apaga todo o conteúdo de uma pasta, mas mantém a pasta."""
    if not os.path.exists(folder):
        print(f"⚠ Pasta não encontrada: {description}")
        return
    try:
        for item in os.listdir(folder):
            item_path = os.path.join(folder, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path, ignore_errors=True)
        print(f"✔ Conteúdo removido de: {description}")
    except Exception as e:
        print(f"✘ Erro ao limpar {description}: {e}")

# ==============================================
# 1. PASTAS PESSOAIS DO USUÁRIO
# ==============================================
def get_user_folders():
    user_profile = os.path.expanduser("~")
    paths = {
        "Desktop": os.path.join(user_profile, "Desktop"),
        "Downloads": os.path.join(user_profile, "Downloads"),
        "Documents": os.path.join(user_profile, "Documents"),
        "Music": os.path.join(user_profile, "Music"),
        "Pictures": os.path.join(user_profile, "Pictures"),
        "Videos": os.path.join(user_profile, "Videos"),
        "OneDrive": os.path.join(user_profile, "OneDrive"),
        "Contacts": os.path.join(user_profile, "Contacts"),
        "Links": os.path.join(user_profile, "Links"),
        "Favorites": os.path.join(user_profile, "Favorites"),
        "Saved Games": os.path.join(user_profile, "Saved Games"),
        "Searches": os.path.join(user_profile, "Searches"),
        "3D Objects": os.path.join(user_profile, "3D Objects"),
    }
    return {nome: pasta for nome, pasta in paths.items() if os.path.exists(pasta)}

def limpar_pastas_pessoais():
    print("\n--- Limpando pastas pessoais ---")
    pastas = get_user_folders()
    for nome, pasta in pastas.items():
        delete_contents(pasta, f"Pasta {nome}")

# ==============================================
# 2. PERFIS DE NAVEGADORES
# ==============================================
def get_browser_paths():
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    browsers = []

    chrome = os.path.join(local_appdata, "Google", "Chrome", "User Data")
    if os.path.exists(chrome):
        browsers.append(chrome)

    edge = os.path.join(local_appdata, "Microsoft", "Edge", "User Data")
    if os.path.exists(edge):
        browsers.append(edge)

    firefox_profiles = os.path.join(appdata, "Mozilla", "Firefox", "Profiles")
    if os.path.exists(firefox_profiles):
        for perfil in os.listdir(firefox_profiles):
            browsers.append(os.path.join(firefox_profiles, perfil))

    brave = os.path.join(local_appdata, "BraveSoftware", "Brave-Browser", "User Data")
    if os.path.exists(brave):
        browsers.append(brave)

    opera = os.path.join(appdata, "Opera Software", "Opera Stable")
    if os.path.exists(opera):
        browsers.append(opera)

    opera_gx = os.path.join(appdata, "Opera Software", "Opera GX Stable")
    if os.path.exists(opera_gx):
        browsers.append(opera_gx)

    vivaldi = os.path.join(local_appdata, "Vivaldi", "User Data")
    if os.path.exists(vivaldi):
        browsers.append(vivaldi)

    return browsers

def limpar_navegadores():
    print("\n--- Limpando perfis de navegadores ---")
    browsers = get_browser_paths()
    for perfil in browsers:
        delete_path(perfil, f"Perfil do navegador: {perfil}")

# ==============================================
# 3. ARQUIVOS TEMPORÁRIOS DO SISTEMA
# ==============================================
def get_temp_folders():
    temp = os.environ.get("TEMP", "")
    win_temp = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Temp")
    prefetch = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Prefetch")
    local_temp = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp")
    internet_cache = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "INetCache")
    recent = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Recent")
    thumbcache = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Explorer")

    pastas = []
    for p in [temp, win_temp, prefetch, local_temp, internet_cache, recent, thumbcache]:
        if p and os.path.exists(p):
            pastas.append(p)
    return pastas

def limpar_temporarios():
    print("\n--- Limpando arquivos temporários ---")
    pastas = get_temp_folders()
    for pasta in pastas:
        delete_contents(pasta, f"Pasta temporária: {pasta}")

# ==============================================
# 4. CACHES ESPECÍFICOS DO WINDOWS
# ==============================================
def limpar_cache_windows():
    print("\n--- Limpando caches do Windows ---")

    # Cache de fontes
    font_cache = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "FontCache")
    if os.path.exists(font_cache):
        delete_contents(font_cache, "Cache de fontes")

    # Cache de ícones
    icon_cache = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Explorer", "iconcache*")
    for f in glob.glob(icon_cache):
        delete_path(f, f"Cache de ícone: {f}")

    # Cache de compatibilidade de programas (AppCompat) – já incluiremos o Amcache separadamente
    appcompat = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "AppCompat", "Programs", "Recent")
    if os.path.exists(appcompat):
        delete_contents(appcompat, "Cache de compatibilidade (Recent)")

    # Cache do Windows Update (SoftwareDistribution)
    softwaredist = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "SoftwareDistribution", "Download")
    if os.path.exists(softwaredist):
        delete_contents(softwaredist, "Arquivos de atualização baixados")

    # Cache do Windows Defender
    defender_quarantine = os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Microsoft", "Windows Defender", "Quarantine")
    if os.path.exists(defender_quarantine):
        delete_contents(defender_quarantine, "Quarentena do Defender")

    # Logs do Windows
    logs = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Logs")
    if os.path.exists(logs):
        delete_contents(logs, "Pastas de logs do Windows")

    # Relatórios de erros do Windows (WER)
    wer = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "WER")
    if os.path.exists(wer):
        delete_contents(wer, "Relatórios de erros")

    # Dumps de memória
    memory_dumps = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Minidump")
    if os.path.exists(memory_dumps):
        delete_contents(memory_dumps, "Minidumps")

    # Arquivos de despejo de memória completa (MEMORY.DMP)
    memory_dmp = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "MEMORY.DMP")
    delete_path(memory_dmp, "Arquivo de despejo de memória")

# ==============================================
# 5. ARQUIVOS DE INSTALAÇÃO ANTIGA (WINDOWS.OLD)
# ==============================================
def limpar_windows_old():
    print("\n--- Removendo Windows.old (se existir) ---")
    windows_old = "C:\\Windows.old"
    if os.path.exists(windows_old):
        print("Tentando adquirir propriedade da pasta Windows.old...")
        run_cmd(f'takeown /F "{windows_old}" /R /D Y', capture=False)
        run_cmd(f'icacls "{windows_old}" /grant Administradores:F /T /Q', capture=False)
        delete_path(windows_old, "Windows.old")
    else:
        print("Nenhum Windows.old encontrado.")

# ==============================================
# 6. PONTOS DE RESTAURAÇÃO DO SISTEMA
# ==============================================
def limpar_pontos_restauracao():
    print("\n--- Removendo pontos de restauração do sistema ---")
    run_powershell("Disable-ComputerRestore -Drive 'C:\\'")
    run_powershell("Enable-ComputerRestore -Drive 'C:\\'")
    print("Pontos de restauração removidos.")

# ==============================================
# 7. LIMPEZA DE REGISTRO (PARTES NÃO CRÍTICAS)
# ==============================================
def limpar_registro():
    print("\n--- Limpando entradas de registro do usuário ---")
    run_cmd('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RunMRU" /va /f', capture=False)
    run_cmd('reg delete "HKCU\\Software\\Microsoft\\Internet Explorer\\TypedURLs" /va /f', capture=False)
    run_cmd('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\WordWheelQuery" /va /f', capture=False)
    run_cmd('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RecentDocs" /va /f', capture=False)
    run_cmd('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\OpenSavePidlMRU" /va /f', capture=False)
    run_cmd('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\LastVisitedPidlMRU" /va /f', capture=False)
    print("Entradas de registro limpas.")

# ==============================================
# 8. CACHES DE REDE (DNS, ARP)
# ==============================================
def limpar_caches_rede():
    print("\n--- Limpando caches de rede ---")
    run_cmd("ipconfig /flushdns", capture=False)
    run_cmd("arp -d *", capture=False)
    run_cmd("nbtstat -R", capture=False)
    run_cmd("nbtstat -RR", capture=False)
    run_cmd("netsh int ip reset", capture=False)
    run_cmd("netsh winsock reset", capture=False)

# ==============================================
# 9. ARQUIVOS DE LOG DO WINDOWS (EVENT VIEWER)
# ==============================================
def limpar_logs_evento():
    print("\n--- Limpando logs de eventos ---")
    logs = ["Application", "System", "Security", "Setup", "ForwardedEvents", "Windows PowerShell"]
    for log in logs:
        run_powershell(f"Clear-EventLog -LogName '{log}'")
        print(f"Log '{log}' limpo.")

# ==============================================
# 10. CACHE DA MICROSOFT STORE
# ==============================================
def limpar_store_cache():
    print("\n--- Limpando cache da Microsoft Store ---")
    run_cmd("wsreset.exe", capture=False)

# ==============================================
# 11. ARQUIVOS DE PÁGINA E HIBERNAÇÃO
# ==============================================
def desabilitar_hibridacao():
    print("\n--- Desabilitando hibernação e removendo arquivo hiberfil.sys ---")
    run_cmd("powercfg -h off", capture=False)

def limpar_pagefile():
    print("\n--- Removendo arquivo de paginação (pagefile.sys) - requer reinicialização ---")
    run_cmd('wmic computersystem where name="%computername%" set AutomaticManagedPagefile=False', capture=False)
    run_cmd('wmic pagefileset where name="C:\\\\pagefile.sys" delete', capture=False)
    print("Arquivo de paginação marcado para remoção. Será efetivado na reinicialização.")

# ==============================================
# 12. ESVAZIAR LIXEIRA
# ==============================================
def esvaziar_lixeira():
    print("\n--- Esvaziando Lixeira ---")
    run_powershell("Clear-RecycleBin -Force")

# ==============================================
# 13. SOBRESCREVER ESPAÇO LIVRE (OPCIONAL, MUITO LENTO)
# ==============================================
def sobrescrever_livre():
    print("\n--- Sobrescrevendo espaço livre na unidade C: (pode levar horas) ---")
    resposta = input("Tem certeza? Isso tornará a recuperação muito difícil, mas é EXTREMAMENTE lento. (s/N): ")
    if resposta.lower() == 's':
        run_cmd("cipher /w:C:\\", capture=False)
    else:
        print("Operação cancelada.")

# ==============================================
# NOVAS FUNÇÕES PARA DESTRUIÇÃO FORENSE AVANÇADA
# ==============================================

def limpar_amcache():
    """Remove o arquivo Amcache.hve e seus artefatos associados."""
    print("\n--- Removendo Amcache (cache de programas executados) ---")
    amcache_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "AppCompat", "Programs")
    if os.path.exists(amcache_dir):
        for arquivo in os.listdir(amcache_dir):
            if "Amcache" in arquivo:
                caminho = os.path.join(amcache_dir, arquivo)
                delete_path(caminho, f"Arquivo Amcache: {arquivo}")
    else:
        print("Pasta AppCompat\\Programs não encontrada.")

def limpar_shimcache():
    """Apaga a chave de registro Shimcache (AppCompatCache)."""
    print("\n--- Removendo Shimcache (cache de compatibilidade) ---")
    run_cmd('reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\AppCompatCache" /va /f', capture=False)

def limpar_usn_journal():
    """Deleta o USN Journal do volume C: (histórico de alterações de arquivos)."""
    print("\n--- Removendo USN Journal (log de alterações NTFS) ---")
    resultado = run_cmd('fsutil usn deletejournal /D C:')
    if "foi excluído" in resultado or "successfully" in resultado:
        print("USN Journal deletado com sucesso.")
    else:
        print("Falha ao deletar USN Journal. Pode ser necessário reiniciar.")

def limpar_shadow_copies():
    """Remove todas as cópias de sombra (Volume Shadow Copies)."""
    print("\n--- Removendo todas as cópias de sombra (Shadow Copies) ---")
    run_cmd('vssadmin delete shadows /all /quiet', capture=False)

def limpar_arquivos_event_log():
    """Apaga fisicamente os arquivos .evtx de logs de eventos."""
    print("\n--- Apagando arquivos de log de eventos (.evtx) ---")
    event_log_dir = os.path.join(os.environ.get("SYSTEMROOT", "C:\\Windows"), "System32", "winevt", "Logs")
    if os.path.exists(event_log_dir):
        # Para evitar erros de arquivo em uso, podemos parar o serviço de log (cuidado!)
        # Aqui vamos tentar parar o serviço, deletar e reiniciar
        run_cmd('net stop EventLog /y', capture=False)
        time.sleep(2)
        delete_contents(event_log_dir, "Arquivos de log de eventos")
        run_cmd('net start EventLog', capture=False)
    else:
        print("Pasta de logs de eventos não encontrada.")

def limpar_telemetria():
    """Desabilita telemetria e remove pastas de diagnóstico."""
    print("\n--- Removendo dados de telemetria do Windows ---")
    # Desabilitar coleta via registro
    run_cmd('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f', capture=False)
    # Pastas comuns de telemetria
    pastas_telemetria = [
        os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Microsoft", "Diagnosis"),
        os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Microsoft", "Windows", "WER"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "WER"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "WebCache"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Internet Explorer", "DOMStore"),
    ]
    for pasta in pastas_telemetria:
        if os.path.exists(pasta):
            delete_path(pasta, f"Pasta de telemetria: {pasta}")

def limpar_backups_locais():
    """Desativa e remove backups locais como File History, OneDrive, etc."""
    print("\n--- Removendo backups locais e sincronizações ---")
    # File History
    run_cmd('reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\FileHistory" /f', capture=False)
    file_history = os.path.join(os.environ.get("USERPROFILE", ""), "File History")
    if os.path.exists(file_history):
        delete_path(file_history, "File History")
    # OneDrive - desinstalar?
    # Desvincula OneDrive (não remove o programa)
    run_cmd('taskkill /f /im OneDrive.exe', capture=False)
    run_cmd('%localappdata%\\Microsoft\\OneDrive\\OneDrive.exe /uninstall', capture=False)
    # Pasta OneDrive já foi limpa em pastas pessoais, mas vamos garantir
    onedrive_folder = os.path.join(os.environ.get("USERPROFILE", ""), "OneDrive")
    delete_path(onedrive_folder, "Pasta OneDrive")
    # Google Drive, Dropbox (se existirem)
    gdrive = os.path.join(os.environ.get("USERPROFILE", ""), "Google Drive")
    dropbox = os.path.join(os.environ.get("USERPROFILE", ""), "Dropbox")
    for p in [gdrive, dropbox]:
        if os.path.exists(p):
            delete_path(p, f"Pasta de sincronização: {p}")

# ==============================================
# NOVA FUNÇÃO: TUDO (COMPLETO + NOVAS FUNÇÕES)
# ==============================================
def limpeza_completa():
    """Executa todas as funções de limpeza, incluindo as forenses."""
    print("\n🔥 INICIANDO LIMPEZA COMPLETA (DESTRUIÇÃO FORENSE) 🔥")
    limpar_pastas_pessoais()
    limpar_navegadores()
    limpar_temporarios()
    limpar_cache_windows()
    limpar_windows_old()
    limpar_pontos_restauracao()
    limpar_registro()
    limpar_caches_rede()
    limpar_logs_evento()
    limpar_store_cache()
    desabilitar_hibridacao()
    limpar_pagefile()
    esvaziar_lixeira()
    # Novas funções
    limpar_amcache()
    limpar_shimcache()
    limpar_usn_journal()
    limpar_shadow_copies()
    limpar_arquivos_event_log()
    limpar_telemetria()
    limpar_backups_locais()

    # Perguntar se deseja sobrescrever espaço livre (opcional, pois é muito demorado)
    print("\n" + "="*60)
    resp = input("Deseja também sobrescrever o espaço livre para dificultar recuperação? (Isso pode levar horas) (s/N): ")
    if resp.lower() == 's':
        sobrescrever_livre()

# ==============================================
# MENU PRINCIPAL
# ==============================================
def menu():
    print("="*70)
    print("🧹 LIMPEZA PROFUNDA DO WINDOWS - MODO 'RECÉM-FORMATADO'")
    print("="*70)
    print("\nEscolha o nível de limpeza:")
    print("1. Básico   (pastas pessoais + navegadores)")
    print("2. Intermediário (básico + temporários + caches do Windows)")
    print("3. Avançado  (intermediário + logs, registro, pontos de restauração, etc.)")
    print("4. Personalizado (escolher itens individualmente)")
    print("5. Sobrescrever espaço livre (após limpeza, opcional)")
    print("6. 🔥 TUDO (Completo - executa todas as funções, inclusive pagefile e hibernação) 🔥")
    print("7. ⚠️  DESTRUIÇÃO FORENSE (inclui Amcache, Shimcache, USN, Shadow Copies, Telemetria, etc.)")
    print("0. Sair")
    return input("Opção: ").strip()

def personalizado():
    print("\n--- Itens disponíveis ---")
    itens = {
        "1": ("Pastas pessoais", limpar_pastas_pessoais),
        "2": ("Navegadores", limpar_navegadores),
        "3": ("Arquivos temporários", limpar_temporarios),
        "4": ("Caches do Windows", limpar_cache_windows),
        "5": ("Windows.old", limpar_windows_old),
        "6": ("Pontos de restauração", limpar_pontos_restauracao),
        "7": ("Registro (partes não críticas)", limpar_registro),
        "8": ("Caches de rede", limpar_caches_rede),
        "9": ("Logs de eventos (Clear-EventLog)", limpar_logs_evento),
        "10": ("Cache da Store", limpar_store_cache),
        "11": ("Desabilitar hibernação", desabilitar_hibridacao),
        "12": ("Remover pagefile (após reboot)", limpar_pagefile),
        "13": ("Esvaziar lixeira", esvaziar_lixeira),
        "14": ("Amcache", limpar_amcache),
        "15": ("Shimcache (registro)", limpar_shimcache),
        "16": ("USN Journal", limpar_usn_journal),
        "17": ("Shadow Copies", limpar_shadow_copies),
        "18": ("Arquivos .evtx de logs", limpar_arquivos_event_log),
        "19": ("Telemetria", limpar_telemetria),
        "20": ("Backups locais (File History, OneDrive)", limpar_backups_locais),
    }
    for chave, (desc, _) in itens.items():
        print(f"{chave}. {desc}")
    escolhas = input("Digite os números separados por vírgula (ex: 1,3,5): ").split(',')
    for e in escolhas:
        e = e.strip()
        if e in itens:
            itens[e][1]()
        else:
            print(f"Opção {e} inválida ignorada.")

def main():
    if not is_admin():
        print("❌ Este script precisa ser executado como Administrador.")
        print("Clique com o botão direito no ícone do Python e escolha 'Executar como administrador'.")
        input("Pressione Enter para sair...")
        sys.exit(1)

    print("\n⚠️  AVISO EXTREMO: Esta limpeza removerá PERMANENTEMENTE todos os seus arquivos pessoais,")
    print("dados de navegadores, logs do sistema, pontos de restauração e muitos outros itens.")
    print("O computador ficará como se tivesse sido recém-formatado, mas o Windows permanecerá instalado.")
    print("Faça um backup COMPLETO de tudo o que for importante antes de continuar.\n")

    while True:
        opcao = menu()
        if opcao == "0":
            print("Saindo...")
            break

        # Confirmação final
        print("\n" + "!"*70)
        confirm = input("Para confirmar, digite o texto exato: 'APAGAR TUDO' (sem aspas): ").strip()
        if confirm != "APAGAR TUDO":
            print("❌ Confirmação incorreta. Operação cancelada.")
            continue

        # Criar ponto de restauração (opcional, mas recomendado)
        criar_ponto = input("Deseja criar um ponto de restauração antes de começar? (s/N): ").strip().lower()
        if criar_ponto == 's':
            run_powershell("Checkpoint-Computer -Description 'Antes da limpeza profunda' -RestorePointType MODIFY_SETTINGS")
            print("Ponto de restauração criado.")

        start = time.time()

        if opcao == "1":
            limpar_pastas_pessoais()
            limpar_navegadores()
            esvaziar_lixeira()
        elif opcao == "2":
            limpar_pastas_pessoais()
            limpar_navegadores()
            limpar_temporarios()
            limpar_cache_windows()
            esvaziar_lixeira()
        elif opcao == "3":
            limpar_pastas_pessoais()
            limpar_navegadores()
            limpar_temporarios()
            limpar_cache_windows()
            limpar_windows_old()
            limpar_pontos_restauracao()
            limpar_registro()
            limpar_caches_rede()
            limpar_logs_evento()
            limpar_store_cache()
            desabilitar_hibridacao()
            esvaziar_lixeira()
        elif opcao == "4":
            personalizado()
            esvaziar_lixeira()
        elif opcao == "5":
            sobrescrever_livre()
        elif opcao == "6":
            limpeza_completa()
        elif opcao == "7":
            print("\n🔥 DESTRUIÇÃO FORENSE AVANÇADA 🔥")
            # Executa todas as funções, incluindo as novas
            limpar_pastas_pessoais()
            limpar_navegadores()
            limpar_temporarios()
            limpar_cache_windows()
            limpar_windows_old()
            limpar_pontos_restauracao()
            limpar_registro()
            limpar_caches_rede()
            limpar_logs_evento()
            limpar_store_cache()
            desabilitar_hibridacao()
            limpar_pagefile()
            esvaziar_lixeira()
            limpar_amcache()
            limpar_shimcache()
            limpar_usn_journal()
            limpar_shadow_copies()
            limpar_arquivos_event_log()
            limpar_telemetria()
            limpar_backups_locais()
            # Pergunta opcional para sobrescrever
            resp = input("\nDeseja sobrescrever espaço livre? (s/N): ")
            if resp.lower() == 's':
                sobrescrever_livre()
        else:
            print("Opção inválida.")
            continue

        elapsed = time.time() - start
        print(f"\n✅ Limpeza concluída em {elapsed:.2f} segundos.")
        print("Recomenda-se reiniciar o computador para aplicar todas as alterações.")

if __name__ == "__main__":
    main()