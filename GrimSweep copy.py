"""
╔══════════════════════════════════════════════════════════════════╗
║              GRIM SWEEP v2.0 - ESTUDO FORENSE                   ║
║  Melhorias: multithreading, multi-usuário, cobertura forense    ║
║             ampliada, log detalhado de operações                ║
╚══════════════════════════════════════════════════════════════════╝

AVISO EDUCACIONAL:
  Este script é desenvolvido para fins de estudo em forense digital,
  privacidade e sanitização de sistemas Windows. Use apenas em
  ambientes próprios ou com autorização explícita.
"""

import os
import shutil
import subprocess
import sys
import ctypes
import time
import glob
import threading
import logging
import winreg
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime



log = logging.getLogger("GrimSweep")
_print_lock = threading.Lock()

stats = {
    "removidos": 0,
    "erros": 0,
    "nao_encontrados": 0,
}
stats_lock = threading.Lock()


def log_ok(msg):
    with stats_lock:
        stats["removidos"] += 1
    log.info(f" {msg}")

def log_warn(msg):
    with stats_lock:
        stats["nao_encontrados"] += 1
    log.warning(f" {msg}")

def log_err(msg):
    with stats_lock:
        stats["erros"] += 1
    log.error(f" {msg}")

def log_info(msg):
    log.info(msg)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_cmd(command, capture=True, timeout=60):
    """Executa um comando no shell com timeout."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=capture,
            text=True, timeout=timeout
        )
        return result.stdout if capture else ""
    except subprocess.TimeoutExpired:
        log_err(f"Timeout ao executar: {command}")
        return ""
    except Exception as e:
        log_err(f"Erro ao executar comando: {command} — {e}")
        return ""

def run_powershell(command, timeout=60):
    """Executa um comando PowerShell com timeout."""
    return run_cmd(f'powershell -NoProfile -NonInteractive -Command "{command}"', timeout=timeout)

def delete_path(path, description):
    """Apaga um arquivo ou pasta com log."""
    if not os.path.exists(path):
        log_warn(f"Não encontrado: {description}")
        return
    try:
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
            log_ok(f"Arquivo removido: {description}")
        elif os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
            log_ok(f"Pasta removida: {description}")
    except Exception as e:
        log_err(f"Erro ao remover {description}: {e}")

def delete_contents(folder, description):
    """Apaga o conteúdo de uma pasta mantendo a estrutura."""
    if not os.path.exists(folder):
        log_warn(f"Pasta não encontrada: {description}")
        return
    try:
        for item in os.listdir(folder):
            item_path = os.path.join(folder, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
            except Exception as e:
                log_err(f"Erro ao remover item {item_path}: {e}")
        log_ok(f"Conteúdo limpo: {description}")
    except Exception as e:
        log_err(f"Erro ao limpar {description}: {e}")

def delete_contents_parallel(folder, description, workers=6):
    """Apaga conteúdo de pasta usando múltiplas threads (performance)."""
    if not os.path.exists(folder):
        log_warn(f"Pasta não encontrada: {description}")
        return
    try:
        items = [os.path.join(folder, i) for i in os.listdir(folder)]
    except Exception as e:
        log_err(f"Erro ao listar {folder}: {e}")
        return

    def _del(path):
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=workers) as ex:
        ex.map(_del, items)

    log_ok(f"Conteúdo limpo (paralelo): {description}")

def get_all_users():
    """
    Retorna lista de (username, profile_path) de todos os usuários
    locais com pasta em C:\\Users, excluindo contas de sistema.
    """
    contas_sistema = {"default", "default user", "public", "all users", "defaultapppool"}
    users_dir = "C:\\Users"
    users = []
    if not os.path.isdir(users_dir):
        return users
    for nome in os.listdir(users_dir):
        if nome.lower() in contas_sistema:
            continue
        caminho = os.path.join(users_dir, nome)
        if os.path.isdir(caminho):
            users.append((nome, caminho))
    return users

def selecionar_usuarios():
    """Exibe usuários disponíveis e deixa o operador escolher."""
    todos = get_all_users()
    if not todos:
        log_warn("Nenhum usuário encontrado em C:\\Users")
        return []

    print("\n--- Usuários disponíveis ---")
    for i, (nome, _) in enumerate(todos, 1):
        print(f"  {i}. {nome}")
    print("  0. TODOS os usuários")

    escolha = input("\nDigite os números separados por vírgula (ou 0 para todos): ").strip()
    if escolha == "0":
        return todos

    selecionados = []
    for parte in escolha.split(","):
        parte = parte.strip()
        if parte.isdigit():
            idx = int(parte) - 1
            if 0 <= idx < len(todos):
                selecionados.append(todos[idx])
    return selecionados


SUBPASTAS_PESSOAIS = [
    "Desktop", "Downloads", "Documents", "Music",
    "Pictures", "Videos", "Contacts", "Links",
    "Favorites", "Saved Games", "Searches", "3D Objects",
    "AppData\\Local\\Temp",
    "AppData\\Roaming\\Microsoft\\Windows\\Recent",
    "AppData\\Roaming\\Microsoft\\Windows\\Recent\\AutomaticDestinations",
    "AppData\\Roaming\\Microsoft\\Windows\\Recent\\CustomDestinations",
]

def limpar_pastas_pessoais(usuarios=None):
    log_info("\n--- Limpando pastas pessoais ---")
    if usuarios is None:
        usuarios = [(os.environ.get("USERNAME", ""), os.path.expanduser("~"))]
    for nome, perfil in usuarios:
        log_info(f"  [Usuário: {nome}]")
        for sub in SUBPASTAS_PESSOAIS:
            caminho = os.path.join(perfil, sub)
            if os.path.exists(caminho):
                delete_contents_parallel(caminho, f"{nome}\\{sub}")

def get_browser_paths_for_user(perfil):
    """Monta lista de caminhos de dados de navegadores para um perfil."""
    local = os.path.join(perfil, "AppData", "Local")
    roaming = os.path.join(perfil, "AppData", "Roaming")
    browsers = []

    candidatos = [
        os.path.join(local, "Google", "Chrome", "User Data"),
        os.path.join(local, "Microsoft", "Edge", "User Data"),
        os.path.join(local, "BraveSoftware", "Brave-Browser", "User Data"),
        os.path.join(local, "Vivaldi", "User Data"),
        os.path.join(local, "Chromium", "User Data"),
        os.path.join(local, "Torch", "User Data"),
        os.path.join(local, "Comodo", "Dragon", "User Data"),
        os.path.join(roaming, "Opera Software", "Opera Stable"),
        os.path.join(roaming, "Opera Software", "Opera GX Stable"),
        os.path.join(roaming, "Opera Software", "Opera Neon"),
        os.path.join(roaming, "Waterfox", "Profiles"),
        os.path.join(roaming, "Pale Moon", "Profiles"),
        os.path.join(roaming, "Thunderbird", "Profiles"), 
    ]
    for c in candidatos:
        if os.path.exists(c):
            browsers.append(c)

    #Firefox
    ff_profiles = os.path.join(roaming, "Mozilla", "Firefox", "Profiles")
    if os.path.exists(ff_profiles):
        for p in os.listdir(ff_profiles):
            browsers.append(os.path.join(ff_profiles, p))

    return browsers

def limpar_navegadores(usuarios=None):
    log_info("\n--- Limpando perfis de navegadores ---")
    if usuarios is None:
        usuarios = [(os.environ.get("USERNAME", ""), os.path.expanduser("~"))]
    for nome, perfil in usuarios:
        log_info(f"  [Usuário: {nome}]")
        for caminho in get_browser_paths_for_user(perfil):
            delete_path(caminho, f"{nome} → {os.path.basename(caminho)}")


def limpar_temporarios(usuarios=None):
    log_info("\n--- Limpando arquivos temporários ---")
    win = os.environ.get("WINDIR", "C:\\Windows")

    pastas_sistema = [
        os.path.join(win, "Temp"),
        os.path.join(win, "Prefetch"),
        os.path.join(win, "SoftwareDistribution", "Download"),
        os.path.join(win, "Minidump"),
        "C:\\Temp",
    ]
    for p in pastas_sistema:
        if os.path.exists(p):
            delete_contents_parallel(p, f"Sistema: {p}")

    if usuarios is None:
        usuarios = [(os.environ.get("USERNAME", ""), os.path.expanduser("~"))]
    for nome, perfil in usuarios:
        sub_temp = [
            os.path.join(perfil, "AppData", "Local", "Temp"),
            os.path.join(perfil, "AppData", "Local", "Microsoft", "Windows", "INetCache"),
            os.path.join(perfil, "AppData", "Local", "Microsoft", "Windows", "WebCache"),
            os.path.join(perfil, "AppData", "Local", "CrashDumps"),
        ]
        for p in sub_temp:
            if os.path.exists(p):
                delete_contents_parallel(p, f"{nome}: {os.path.basename(p)}")


def limpar_cache_windows(usuarios=None):
    log_info("\n--- Limpando caches do Windows ---")
    local_app = os.environ.get("LOCALAPPDATA", "")
    win = os.environ.get("WINDIR", "C:\\Windows")
    prog_data = os.environ.get("PROGRAMDATA", "C:\\ProgramData")

    pastas = [
        (os.path.join(local_app, "Microsoft", "Windows", "FontCache"), "Cache de fontes"),
        (os.path.join(win, "AppCompat", "Programs", "Recent"), "AppCompat Recent"),
        (os.path.join(prog_data, "Microsoft", "Windows Defender", "Quarantine"), "Defender Quarantine"),
        (os.path.join(win, "Logs"), "Logs do Windows"),
        (os.path.join(local_app, "Microsoft", "Windows", "WER"), "WER Local"),
        (os.path.join(prog_data, "Microsoft", "Windows", "WER"), "WER ProgramData"),
        (os.path.join(local_app, "Microsoft", "Windows", "Explorer"), "Explorer cache"),
        (os.path.join(local_app, "D3DSCache"), "DirectX Shader Cache"),
        (os.path.join(local_app, "NVIDIA", "DXCache"), "NVIDIA DXCache"),
        (os.path.join(local_app, "NVIDIA", "GLCache"), "NVIDIA GLCache"),
        (os.path.join(prog_data, "Microsoft", "Windows", "WER", "ReportArchive"), "WER ReportArchive"),
        (os.path.join(prog_data, "Microsoft", "Windows", "WER", "ReportQueue"), "WER ReportQueue"),
        (os.path.join(win, "Logs", "CBS"), "CBS Logs"),
        (os.path.join(win, "inf", "setupapi.dev.log"), "SetupAPI log"),
    ]

    for pasta, desc in pastas:
        if os.path.isfile(pasta):
            delete_path(pasta, desc)
        elif os.path.isdir(pasta):
            delete_contents_parallel(pasta, desc)

    #Iconcache via glob
    for f in glob.glob(os.path.join(local_app, "Microsoft", "Windows", "Explorer", "iconcache*")):
        delete_path(f, f"iconcache: {os.path.basename(f)}")
    for f in glob.glob(os.path.join(local_app, "Microsoft", "Windows", "Explorer", "thumbcache*")):
        delete_path(f, f"thumbcache: {os.path.basename(f)}")

    #Por usuário
    if usuarios:
        for nome, perfil in usuarios:
            extra = [
                os.path.join(perfil, "AppData", "Local", "D3DSCache"),
                os.path.join(perfil, "AppData", "Local", "Microsoft", "Windows", "Caches"),
            ]
            for p in extra:
                if os.path.exists(p):
                    delete_contents_parallel(p, f"{nome}: {os.path.basename(p)}")

def limpar_lnk_jumplist(usuarios=None):
    """
    [FORENSE] Remove arquivos .lnk (atalhos recentes) e JumpLists.
    Esses arquivos registram quais arquivos foram abertos e quando.
    """
    log_info("\n--- [FORENSE] Removendo .lnk e JumpLists ---")
    if usuarios is None:
        usuarios = [(os.environ.get("USERNAME", ""), os.path.expanduser("~"))]
    for nome, perfil in usuarios:
        caminhos = [
            os.path.join(perfil, "AppData", "Roaming", "Microsoft", "Windows", "Recent"),
            os.path.join(perfil, "AppData", "Roaming", "Microsoft", "Windows", "Recent", "AutomaticDestinations"),
            os.path.join(perfil, "AppData", "Roaming", "Microsoft", "Windows", "Recent", "CustomDestinations"),
        ]
        for c in caminhos:
            if os.path.exists(c):
                delete_contents_parallel(c, f"{nome}: JumpList/Recent")

def limpar_prefetch():
    """
    [FORENSE] Remove arquivos Prefetch (.pf).
    Contêm nomes e timestamps de execução de programas.
    """
    log_info("\n--- [FORENSE] Removendo Prefetch ---")
    prefetch = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Prefetch")
    if os.path.exists(prefetch):
        delete_contents_parallel(prefetch, "Prefetch")

def limpar_mru_registro(usuarios=None):
    """
    [FORENSE] Remove MRU (Most Recently Used) do registro.
    MRUs guardam histórico de arquivos abertos, URLs digitadas, comandos Run.
    """
    log_info("\n--- [FORENSE] Limpando MRU no registro ---")
    chaves_hkcu = [
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU",
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs",
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU",
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU",
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\WordWheelQuery",
        r"Software\Microsoft\Internet Explorer\TypedURLs",
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths",
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\SearchHistory",
        r"Software\Microsoft\Windows NT\CurrentVersion\Network\Persistent Connections",
        r"Software\Microsoft\Windows\CurrentVersion\ActivityDataModel",
    ]
    for chave in chaves_hkcu:
        run_cmd(f'reg delete "HKCU\\{chave}" /va /f', capture=False)

    #limpar UserAssist
    run_cmd(
        r'reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist" /va /f',
        capture=False
    )
    log_ok("MRU e UserAssist limpos")

def limpar_userassist():
    """
    [FORENSE] UserAssist codifica (ROT13) cada programa executado com
    contador de execuções e timestamp. Altamente relevante em forense.
    """
    log_info("\n--- [FORENSE] Removendo UserAssist ---")
    run_cmd(
        r'reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist" /f',
        capture=False
    )
    log_ok("UserAssist removido")

def limpar_bam_dam():
    """
    [FORENSE] BAM (Background Activity Moderator) e DAM registram
    processos em background com timestamps — artefato forense crítico.
    """
    log_info("\n--- [FORENSE] Removendo BAM/DAM ---")
    run_cmd(
        r'reg delete "HKLM\SYSTEM\CurrentControlSet\Services\bam\State\UserSettings" /f',
        capture=False
    )
    run_cmd(
        r'reg delete "HKLM\SYSTEM\CurrentControlSet\Services\dam\State\UserSettings" /f',
        capture=False
    )
    log_ok("BAM/DAM limpos")

def limpar_srum():
    """
    [FORENSE] SRUM (System Resource Usage Monitor) — banco de dados que
    registra uso de CPU, rede e energia por processo nas últimas 30-60 dias.
    Arquivo: C:\\Windows\\System32\\sru\\SRUDB.dat
    """
    log_info("\n--- [FORENSE] Removendo SRUM (System Resource Usage Monitor) ---")
    srum = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System32", "sru")
    if os.path.exists(srum):
        run_cmd("net stop DiagTrack /y", capture=False)
        run_cmd("net stop WdiServiceHost /y", capture=False)
        time.sleep(1)
        delete_contents_parallel(srum, "SRUM database")
    else:
        log_warn("Pasta SRUM não encontrada")

def limpar_shellbags():
    """
    [FORENSE] ShellBags registram quais pastas foram abertas no Explorer,
    mesmo após a pasta ser deletada. Artefato clássico em forense.
    """
    log_info("\n--- [FORENSE] Removendo ShellBags ---")
    chaves = [
        r"HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\BagMRU",
        r"HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\Bags",
        r"HKCU\Software\Microsoft\Windows\Shell\BagMRU",
        r"HKCU\Software\Microsoft\Windows\Shell\Bags",
    ]
    for chave in chaves:
        run_cmd(f'reg delete "{chave}" /f', capture=False)
    log_ok("ShellBags removidos")

def limpar_thumbsdb():
    """
    [FORENSE] Remove arquivos Thumbs.db e ehthumbs.db recursivamente.
    Esses arquivos guardam miniaturas de imagens visualizadas.
    """
    log_info("\n--- [FORENSE] Removendo Thumbs.db recursivos ---")
    drives = ["C:\\"]
    for drive in drives:
        for root, dirs, files in os.walk(drive):
            # Evitar pastas de sistema críticas
            dirs[:] = [d for d in dirs if d.lower() not in
                       {"windows", "program files", "program files (x86)"}]
            for f in files:
                if f.lower() in ("thumbs.db", "ehthumbs.db", "desktop.ini"):
                    caminho = os.path.join(root, f)
                    try:
                        os.remove(caminho)
                    except Exception:
                        pass
    log_ok("Thumbs.db removidos")

def limpar_timeline_windows():
    """
    [FORENSE] Remove o banco de dados de Timeline do Windows 10/11,
    que registra atividade do usuário cronologicamente.
    """
    log_info("\n--- [FORENSE] Removendo Timeline do Windows ---")
    run_cmd(
        r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" /v EnableActivityFeed /t REG_DWORD /d 0 /f',
        capture=False
    )
    conn_data = os.path.join(
        os.environ.get("LOCALAPPDATA", ""), #DB
        "ConnectedDevicesPlatform"
    )
    if os.path.exists(conn_data):
        delete_contents_parallel(conn_data, "Timeline ConnectedDevicesPlatform")
    log_ok("Timeline desabilitada e dados removidos")

def limpar_wer_completo():
    """
    [FORENSE] Remove todos os relatórios de erro do Windows (WER)
    incluindo crash dumps associados.
    """
    log_info("\n--- [FORENSE] Limpando WER completo ---")
    pastas = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "WER"),
        os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Microsoft", "Windows", "WER"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Minidump"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "LiveKernelReports"),
    ]
    mem_dmp = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "MEMORY.DMP")
    delete_path(mem_dmp, "MEMORY.DMP")
    for p in pastas:
        if os.path.exists(p):
            delete_contents_parallel(p, f"WER: {os.path.basename(p)}")

def limpar_powershell_history(usuarios=None):
    """
    [FORENSE] Remove histórico de comandos do PowerShell.
    Armazenado por padrão em AppData\\Roaming\\Microsoft\\Windows\\PowerShell\\PSReadline\\
    """
    log_info("\n--- [FORENSE] Removendo histórico do PowerShell ---")
    if usuarios is None:
        usuarios = [(os.environ.get("USERNAME", ""), os.path.expanduser("~"))]
    for nome, perfil in usuarios:
        hist = os.path.join(
            perfil, "AppData", "Roaming", "Microsoft",
            "Windows", "PowerShell", "PSReadline", "ConsoleHost_history.txt"
        )
        if os.path.exists(hist):
            delete_path(hist, f"{nome}: PowerShell history")

def limpar_cmd_history():
    """
    [FORENSE] Remove histórico de comandos do CMD (doskey).
    """
    log_info("\n--- [FORENSE] Limpando histórico CMD ---")
    run_cmd("doskey /reinstall", capture=False)
    log_ok("Histórico CMD limpo (sessão atual)")

def limpar_registro_completo():
    """
    [FORENSE] Limpeza ampliada do registro — inclui itens do original
    mais novos artefatos forenses relevantes.
    """
    log_info("\n--- Limpando registro (ampliado) ---")
    entradas = [
        r'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU',
        r'HKCU\Software\Microsoft\Internet Explorer\TypedURLs',
        r'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\WordWheelQuery',
        r'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs',
        r'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU',
        r'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU',
        r'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\SearchHistory',
        r'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths',
        r'HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR',
        r'HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\NetworkList\Profiles',
        r'HKCU\Network',
        r'HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache',
    ]
    for chave in entradas:
        run_cmd(f'reg delete "{chave}" /va /f', capture=False)
    log_ok("Registro ampliado limpo")


def limpar_windows_old():
    log_info("\n--- Removendo Windows.old ---")
    windows_old = "C:\\Windows.old"
    if os.path.exists(windows_old):
        run_cmd(f'takeown /F "{windows_old}" /R /D Y', capture=False)
        run_cmd(f'icacls "{windows_old}" /grant Administradores:F /T /Q', capture=False)
        delete_path(windows_old, "Windows.old")
    else:
        log_warn("Windows.old não encontrado")

def limpar_pontos_restauracao():
    log_info("\n--- Removendo pontos de restauração ---")
    run_powershell("Disable-ComputerRestore -Drive 'C:\\'")
    run_powershell("Enable-ComputerRestore -Drive 'C:\\'")
    log_ok("Pontos de restauração removidos")

def limpar_caches_rede():
    log_info("\n--- Limpando caches de rede ---")
    cmds = [
        "ipconfig /flushdns",
        "arp -d *",
        "nbtstat -R",
        "nbtstat -RR",
        "netsh int ip reset",
        "netsh winsock reset",
        'cmdkey /list | findstr "Target" | for /f "tokens=2 delims= " %i in (\'more\') do cmdkey /delete:%i',
    ]
    for cmd in cmds:
        run_cmd(cmd, capture=False)
    log_ok("Caches de rede limpos (requer reinicialização para reset do Winsock)")

def limpar_logs_evento():
    log_info("\n--- Limpando logs de eventos ---")
    logs = ["Application", "System", "Security", "Setup",
            "ForwardedEvents", "Windows PowerShell",
            "Microsoft-Windows-PowerShell/Operational",
            "Microsoft-Windows-TaskScheduler/Operational",  # NOVO
            "Microsoft-Windows-TerminalServices-LocalSessionManager/Operational",  # NOVO (RDP)
            ]
    for l in logs:
        run_powershell(f"wevtutil cl '{l}'")
    log_ok("Logs de eventos limpos")

def limpar_store_cache():
    log_info("\n--- Limpando cache da Microsoft Store ---")
    run_cmd("wsreset.exe", capture=False)

def desabilitar_hibernacao():
    log_info("\n--- Desabilitando hibernação (hiberfil.sys) ---")
    run_cmd("powercfg -h off", capture=False)
    log_ok("Hibernação desabilitada")

def limpar_pagefile():
    log_info("\n--- Removendo pagefile.sys ---")
    run_cmd('wmic computersystem where name="%computername%" set AutomaticManagedPagefile=False', capture=False)
    run_cmd('wmic pagefileset where name="C:\\\\pagefile.sys" delete', capture=False)
    log_ok("Pagefile marcado para remoção (efetivado no próximo boot)")

def esvaziar_lixeira():
    log_info("\n--- Esvaziando Lixeira ---")
    run_powershell("Clear-RecycleBin -Force -ErrorAction SilentlyContinue")
    log_ok("Lixeira esvaziada")

def limpar_amcache():
    log_info("\n--- Removendo Amcache ---")
    amcache_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "AppCompat", "Programs")
    if os.path.exists(amcache_dir):
        for arq in os.listdir(amcache_dir):
            if "Amcache" in arq:
                delete_path(os.path.join(amcache_dir, arq), f"Amcache: {arq}")
    else:
        log_warn("Pasta AppCompat\\Programs não encontrada")

def limpar_shimcache():
    log_info("\n--- Removendo Shimcache ---")
    run_cmd(
        r'reg delete "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\AppCompatCache" /va /f',
        capture=False
    )
    log_ok("Shimcache limpo")

def limpar_usn_journal():
    log_info("\n--- Removendo USN Journal ---")
    resultado = run_cmd("fsutil usn deletejournal /D C:")
    if resultado and ("excluído" in resultado.lower() or "success" in resultado.lower()):
        log_ok("USN Journal deletado")
    else:
        log_warn("Falha no USN Journal — pode requerer reinicialização")

def limpar_shadow_copies():
    log_info("\n--- Removendo Shadow Copies ---")
    run_cmd("vssadmin delete shadows /all /quiet", capture=False)
    log_ok("Shadow Copies removidas")

def limpar_arquivos_event_log():
    log_info("\n--- Apagando arquivos .evtx ---")
    event_dir = os.path.join(os.environ.get("SYSTEMROOT", "C:\\Windows"), "System32", "winevt", "Logs")
    if os.path.exists(event_dir):
        run_cmd("net stop EventLog /y", capture=False)
        time.sleep(2)
        delete_contents_parallel(event_dir, "Arquivos .evtx")
        run_cmd("net start EventLog", capture=False)
    else:
        log_warn("Pasta de logs de eventos não encontrada")

def limpar_telemetria():
    log_info("\n--- Removendo telemetria ---")
    run_cmd(
        r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
        capture=False
    )
    pastas = [
        os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Microsoft", "Diagnosis"),
        os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Microsoft", "Windows", "WER"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "WER"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "WebCache"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Internet Explorer", "DOMStore"),
        # NOVO: DiagTrack
        os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Microsoft", "DiagnosticLogCSP"),
    ]
    for p in pastas:
        if os.path.exists(p):
            delete_path(p, f"Telemetria: {os.path.basename(p)}")

def limpar_backups_locais():
    log_info("\n--- Removendo backups e sincronizações ---")
    run_cmd(r'reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\FileHistory" /f', capture=False)
    file_history = os.path.join(os.environ.get("USERPROFILE", ""), "File History")
    if os.path.exists(file_history):
        delete_path(file_history, "File History")
    run_cmd("taskkill /f /im OneDrive.exe", capture=False)
    run_cmd("%localappdata%\\Microsoft\\OneDrive\\OneDrive.exe /uninstall", capture=False)
    for pasta_nome in ["OneDrive", "Google Drive", "Dropbox", "Box", "iCloudDrive"]:
        p = os.path.join(os.environ.get("USERPROFILE", ""), pasta_nome)
        if os.path.exists(p):
            delete_path(p, f"Sync: {pasta_nome}")

def sobrescrever_livre():
    log_info("\n--- Sobrescrevendo espaço livre (cipher /w) ---")
    resposta = input("ATENÇÃO: Isso pode levar HORAS. Confirma? (s/N): ")
    if resposta.lower() == "s":
        run_cmd("cipher /w:C:\\", capture=False, timeout=86400)
        log_ok("Espaço livre sobrescrito")
    else:
        log_info("Operação cancelada pelo usuário.")


def limpeza_basica(usuarios):
    limpar_pastas_pessoais(usuarios)
    limpar_navegadores(usuarios)
    esvaziar_lixeira()

def limpeza_intermediaria(usuarios):
    limpeza_basica(usuarios)
    limpar_temporarios(usuarios)
    limpar_cache_windows(usuarios)

def limpeza_avancada(usuarios):
    limpeza_intermediaria(usuarios)
    limpar_windows_old()
    limpar_pontos_restauracao()
    limpar_registro_completo()
    limpar_caches_rede()
    limpar_logs_evento()
    limpar_store_cache()
    desabilitar_hibernacao()

def limpeza_forense(usuarios):
    """Limpeza máxima — todos os artefatos forenses."""
    limpeza_avancada(usuarios)
    limpar_pagefile()
    limpar_amcache()
    limpar_shimcache()
    limpar_usn_journal()
    limpar_shadow_copies()
    limpar_arquivos_event_log()
    limpar_telemetria()
    limpar_backups_locais()
    limpar_lnk_jumplist(usuarios)
    limpar_prefetch()
    limpar_mru_registro(usuarios)
    limpar_userassist()
    limpar_bam_dam()
    limpar_srum()
    limpar_shellbags()
    limpar_timeline_windows()
    limpar_wer_completo()
    limpar_powershell_history(usuarios)
    limpar_cmd_history()
    esvaziar_lixeira()

def personalizado(usuarios):
    itens = {
        "1":  ("Pastas pessoais",               lambda: limpar_pastas_pessoais(usuarios)),
        "2":  ("Navegadores",                    lambda: limpar_navegadores(usuarios)),
        "3":  ("Temporários",                    lambda: limpar_temporarios(usuarios)),
        "4":  ("Caches Windows",                 lambda: limpar_cache_windows(usuarios)),
        "5":  ("Windows.old",                    limpar_windows_old),
        "6":  ("Pontos de restauração",          limpar_pontos_restauracao),
        "7":  ("Registro ampliado",              limpar_registro_completo),
        "8":  ("Caches de rede",                 limpar_caches_rede),
        "9":  ("Logs de eventos",                limpar_logs_evento),
        "10": ("Cache da Store",                 limpar_store_cache),
        "11": ("Hibernação",                     desabilitar_hibernacao),
        "12": ("Pagefile",                       limpar_pagefile),
        "13": ("Lixeira",                        esvaziar_lixeira),
        "14": ("Amcache",                        limpar_amcache),
        "15": ("Shimcache",                      limpar_shimcache),
        "16": ("USN Journal",                    limpar_usn_journal),
        "17": ("Shadow Copies",                  limpar_shadow_copies),
        "18": ("Arquivos .evtx",                 limpar_arquivos_event_log),
        "19": ("Telemetria",                     limpar_telemetria),
        "20": ("Backups / sync",                 limpar_backups_locais),
        "21": ("[FORENSE] LNK + JumpLists",      lambda: limpar_lnk_jumplist(usuarios)),
        "22": ("[FORENSE] Prefetch",             limpar_prefetch),
        "23": ("[FORENSE] MRU registro",         lambda: limpar_mru_registro(usuarios)),
        "24": ("[FORENSE] UserAssist",           limpar_userassist),
        "25": ("[FORENSE] BAM/DAM",              limpar_bam_dam),
        "26": ("[FORENSE] SRUM",                 limpar_srum),
        "27": ("[FORENSE] ShellBags",            limpar_shellbags),
        "28": ("[FORENSE] Timeline Windows",     limpar_timeline_windows),
        "29": ("[FORENSE] WER completo",         limpar_wer_completo),
        "30": ("[FORENSE] PowerShell history",   lambda: limpar_powershell_history(usuarios)),
        "31": ("[FORENSE] CMD history",          limpar_cmd_history),
        "32": ("[FORENSE] Thumbs.db recursivo",  limpar_thumbsdb),
    }
    print("\n--- Itens disponíveis ---")
    for k, (desc, _) in itens.items():
        print(f"  {k:>3}. {desc}")
    escolhas = input("\nDigite os números separados por vírgula: ").split(",")
    for e in escolhas:
        e = e.strip()
        if e in itens:
            itens[e][1]()
        else:
            log_warn(f"Opção inválida ignorada: {e}")

def menu():
    print("\n" + "="*70)
    print("  GRIM SWEEP v2.0")
    print("="*70)
    print("  1. Básico       (pastas pessoais + navegadores)")
    print("  2. Intermediário (+ temporários + caches)")
    print("  3. Avançado     (+ logs, registro, rede, restauração)")
    print("  4. Personalizado")
    print("  5. Sobrescrever espaço livre")
    print("  6. TUDO — Limpeza forense completa")
    print("  0. Sair")
    print("="*70)
    return input("  Opção: ").strip()

def imprimir_relatorio(elapsed):
    print("\n" + "="*60)
    print("  RELATÓRIO FINAL")
    print("="*60)
    print(f"  Itens removidos  : {stats['removidos']}")
    print(f"  Não encontrados  : {stats['nao_encontrados']}")
    print(f"  Erros            : {stats['erros']}")
    print(f"  Tempo total      : {elapsed:.2f}s")
    print("="*60)
    print("  Recomenda-se reiniciar o computador.")


# ──────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────

def main():
    if not is_admin():
        print("\n[ERRO] Este script precisa ser executado como Administrador.")
        input("Pressione Enter para sair...")
        sys.exit(1)

    # Seleção de usuários para operações multi-usuário
    print("Selecione os usuários a serem afetados:")
    usuarios = selecionar_usuarios()
    if not usuarios:
        print("Nenhum usuário selecionado. Usando usuário atual.")
        usuarios = [(os.environ.get("USERNAME", ""), os.path.expanduser("~"))]

    start = time.time()

    while True:
        opcao = menu()
        if opcao == "0":
            print("Saindo...")
            break
        elif opcao == "1":
            limpeza_basica(usuarios)
        elif opcao == "2":
            limpeza_intermediaria(usuarios)
        elif opcao == "3":
            limpeza_avancada(usuarios)
        elif opcao == "4":
            personalizado(usuarios)
        elif opcao == "5":
            sobrescrever_livre()
        elif opcao == "6":
            limpeza_forense(usuarios)
            resp = input("\nDeseja sobrescrever espaço livre também? (s/N): ")
            if resp.lower() == "s":
                sobrescrever_livre()
        else:
            print("Opção inválida.")
            continue

        imprimir_relatorio(time.time() - start)

if __name__ == "__main__":
    main()