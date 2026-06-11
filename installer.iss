; ============================================================
;  Ultimate Download MP4 - Instalador (Inno Setup)
;  Estilo "assistente classico" (parecido com o do Node.js):
;   - Pagina de boas-vindas com IMAGEM LATERAL grande;
;   - Pagina de LICENCA (aceitar os termos);
;   - Escolha da pasta de destino;
;   - "Configuracao personalizada" com ARVORE DE COMPONENTES;
;   - Barra de progresso e pagina de conclusao;
;   - Desinstalador registrado no Windows.
;
;  Compilar: duplo clique em build_installer.bat
;  Pre-requisito: dist\UltimateDownloadMP4.exe (rode build.bat antes).
; ============================================================

#define AppName "Ultimate Download MP4"
#define AppVersion "2.0.0"
#define AppPublisher "Ultimate Download MP4"
#define AppExeName "UltimateDownloadMP4.exe"

[Setup]
AppId={{B7E1B2B0-3C44-4F5A-9E21-7A2D6C8F1E90}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
PrivilegesRequiredOverridesAllowed=dialog

; --- Saida (na propria pasta do projeto, nao numa subpasta) ---
OutputDir=.
OutputBaseFilename=UltimateDownloadMP4-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes

; --- Visual estilo Node.js (assistente classico com imagem lateral) ---
WizardStyle=modern
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
WizardImageFile=assets\wizard_large.bmp
WizardSmallImageFile=assets\wizard_small.bmp
WizardImageStretch=yes
; Mostra a pagina de licenca antes de instalar.
LicenseFile=LICENSE.txt
; Sempre exibir a pagina de "pronto para instalar" com o resumo.
DisableReadyPage=no

; --- Apenas Windows 64 bits ---
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

; ------------------------------------------------------------
;  Tipos de instalacao (aparecem na pagina "Configuracao
;  personalizada", como no instalador do Node.js).
; ------------------------------------------------------------
[Types]
Name: "full"; Description: "{cm:FullInstallation}"
Name: "custom"; Description: "{cm:CustomInstallation}"; Flags: iscustom

; ------------------------------------------------------------
;  Arvore de componentes (recursos selecionaveis).
; ------------------------------------------------------------
[Components]
Name: "main"; Description: "{#AppName}"; Types: full custom; Flags: fixed
Name: "shortcuts"; Description: "{cm:Shortcuts}"; Types: full custom
Name: "shortcuts\startmenu"; Description: "{cm:StartMenuShortcut}"; Types: full custom
Name: "shortcuts\desktop"; Description: "{cm:DesktopShortcut}"; Types: full custom

[Files]
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Components: main; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Components: main; Flags: ignoreversion isreadme
Source: "LICENSE.txt"; DestDir: "{app}"; Components: main; Flags: ignoreversion

[Icons]
; Menu Iniciar (conforme o componente selecionado).
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Components: shortcuts\startmenu
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"; Components: shortcuts\startmenu
; Area de Trabalho.
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Components: shortcuts\desktop

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

; ------------------------------------------------------------
;  Textos personalizados (PT-BR e EN) usados acima via {cm:...}.
; ------------------------------------------------------------
[CustomMessages]
brazilianportuguese.FullInstallation=Instalacao completa
brazilianportuguese.CustomInstallation=Instalacao personalizada
brazilianportuguese.Shortcuts=Atalhos
brazilianportuguese.StartMenuShortcut=Atalho no Menu Iniciar
brazilianportuguese.DesktopShortcut=Atalho na Area de Trabalho
english.FullInstallation=Full installation
english.CustomInstallation=Custom installation
english.Shortcuts=Shortcuts
english.StartMenuShortcut=Start Menu shortcut
english.DesktopShortcut=Desktop shortcut
