import os
import subprocess
import fitz
from pathlib import Path

# ⚠️ LOCAL (WINDOWS): DIMITRIUS
#SOFFICE = r"D:\Program Files\LibreOffice\program\soffice.exe"  # <-- PARA PRODUÇÃO: deixe vazio ou remova e use 'soffice' no
SOFFICE = None

def get_soffice_cmd() -> str:
    """
    Descobre qual comando usar para chamar o LibreOffice.
    - Se SOFFICE estiver definido e existir, usa ele.
    - Senão, usa 'soffice' (para ambientes como Docker/Cloud Run com libreoffice instalado no PATH).
    """
    if SOFFICE and Path(SOFFICE).exists():
        return SOFFICE
    return "soffice"


def xlsx_to_pdf(xlsx_path: str, pdf_path: str | None = None) -> str:
    """
    Converte um XLSX em PDF usando LibreOffice (soffice) em modo headless.
    Retorna o caminho do PDF gerado.
    """
    xlsx_path = os.path.abspath(xlsx_path)
    xlsx_file = Path(xlsx_path)

    if not xlsx_file.exists():
        raise FileNotFoundError(f"XLSX não encontrado: {xlsx_path}")

    # Diretório de saída
    if pdf_path is None:
        out_dir = xlsx_file.parent
        pdf_name = xlsx_file.with_suffix(".pdf").name
        pdf_path = out_dir / pdf_name
    else:
        pdf_path = Path(pdf_path)
        out_dir = pdf_path.parent

    out_dir.mkdir(parents=True, exist_ok=True)

    soffice_cmd = get_soffice_cmd()

    cmd = [
        soffice_cmd,
        "--headless",
        "--convert-to", "pdf",
        "--outdir", str(out_dir),
        str(xlsx_file),
    ]

    # Roda o LibreOffice pra converter
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Erro ao converter XLSX para PDF:\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )

    # LibreOffice gera o PDF com o mesmo nome base do XLSX
    return str(pdf_path)

def manter_apenas_primeira_pagina(pdf_path: str):
    """
    Mantém apenas a primeira página do PDF.
    Sobrescreve o arquivo original.
    """
    from pathlib import Path
    import fitz

    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

    doc = fitz.open(str(pdf_path))

    # Criar novo PDF só com a página 0
    new_doc = fitz.open()
    new_doc.insert_pdf(doc, from_page=0, to_page=0)

    temp_path = pdf_path.with_name("temp_" + pdf_path.name)
    new_doc.save(str(temp_path))
    new_doc.close()
    doc.close()

    # substituir o arquivo original
    temp_path.replace(pdf_path)

    print(f"PDF reduzido para apenas 1 página: {pdf_path}")


def aplicar_marca_dagua_fitz(pdf_path: str):
    """
    Aplica marca d'água no PDF já convertido usando PyMuPDF (fitz).
    O PDF original é sobrescrito.
    """
    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

    doc = fitz.open(str(pdf_path))

    texto1 = "  Emitido via"
    texto2 = "SGU Express"

    for page in doc:
        width, height = page.rect.width, page.rect.height
        rotacao = page.rotation  # 0 para portrait, 90 para landscape

        if rotacao == 90:
            x = 26
            y = 75
            angle = 90
            page.insert_text(
                (x, y), texto1, fontsize=9, color=(0.5, 0.5, 0.5),
                rotate=angle, overlay=True
            )
            page.insert_text(
                (x + 10, y), texto2, fontsize=9, color=(0.5, 0.5, 0.5),
                rotate=angle, overlay=True
            )

        else:
            x = width - 75
            y = 25
            angle = 0
            page.insert_text(
                (x, y), texto1, fontsize=9, color=(0.5, 0.5, 0.5),
                rotate=angle, overlay=True
            )
            page.insert_text(
                (x, y + 11), texto2, fontsize=9, color=(0.5, 0.5, 0.5),
                rotate=angle, overlay=True
            )

    temp_path = pdf_path.with_name(f"temp_{pdf_path.name}")
    doc.save(temp_path)
    doc.close()

    temp_path.replace(pdf_path)

    print(f"Marca d'água aplicada com sucesso: {pdf_path}")

def gerar_pdf_com_marca(xlsx_path: str) -> str:
    """
    Converte um .xlsx em PDF e aplica marca d'água automaticamente.
    Retorna o caminho final do PDF.
    """
    # 1) converter para PDF
    pdf_path = xlsx_to_pdf(xlsx_path)

    # 2) aplicar marca d’água
    aplicar_marca_dagua_fitz(pdf_path)

    return pdf_path

def gerar_pdf_final(xlsx_path: str) -> str:
    """
    Converte XLSX em PDF, aplica marca d'água e mantém apenas a primeira página.
    Retorna o caminho final do PDF gerado.
    """
    # 1) Converter para PDF
    pdf_path = xlsx_to_pdf(xlsx_path)

    # 2) Aplicar marca d'água
    aplicar_marca_dagua_fitz(pdf_path)

    # 3) Reduzir para apenas 1 página
    manter_apenas_primeira_pagina(pdf_path)

    return pdf_path


if __name__ == "__main__":
    from pathlib import Path

    base_dir = Path(__file__).resolve().parent
    xlsx_files = list(base_dir.glob("*.xlsx"))

    if not xlsx_files:
        print("Nenhum arquivo .xlsx encontrado na mesma pasta do script.")
    else:
        print(f"Encontrados {len(xlsx_files)} arquivo(s) .xlsx:")
        for f in xlsx_files:
            print(" -", f.name)

        print("\nIniciando conversão para PDF + marca d'água + corte para 1 página...\n")

        for f in xlsx_files:
            try:
                # 1) Converter XLSX → PDF
                pdf_path = xlsx_to_pdf(str(f))
                print(f"[OK] PDF gerado: {Path(pdf_path).name}")

                # 2) Aplicar marca d'água
                aplicar_marca_dagua_fitz(pdf_path)
                print(f"[OK] Marca d'água aplicada: {Path(pdf_path).name}")

                # 3) Garantir apenas a primeira página
                manter_apenas_primeira_pagina(pdf_path)
                print(f"[OK] PDF reduzido para 1 página: {Path(pdf_path).name}\n")

            except Exception as e:
                print(f"[FALHA] {f.name}: {e}\n")