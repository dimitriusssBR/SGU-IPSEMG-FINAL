import os
import subprocess
import fitz
from pathlib import Path

# ⚠️ LOCAL (WINDOWS): DIMITRIUS
#SOFFICE = r"D:\Program Files\LibreOffice\program\soffice.exe"
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


def manter_apenas_primeira_pagina(pdf_path: str) -> str:
    """
    Mantém apenas a primeira página do PDF.
    NÃO sobrescreve o original. Gera: <nome>_1pag.pdf
    Retorna o caminho do novo PDF.
    """
    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

    doc = fitz.open(str(pdf_path))

    # Criar novo PDF só com a página 0
    new_doc = fitz.open()
    new_doc.insert_pdf(doc, from_page=0, to_page=0)

    out_path = pdf_path.with_name(pdf_path.stem + "_1pag.pdf")
    new_doc.save(str(out_path))
    new_doc.close()
    doc.close()

    print(f"PDF reduzido para apenas 1 página: {out_path}")
    return str(out_path)


def aplicar_marca_dagua_fitz(pdf_path: str) -> str:
    """
    Aplica marca d'água no PDF usando PyMuPDF (fitz).
    NÃO sobrescreve o original. Gera: <nome>_marca.pdf
    Retorna o caminho do PDF com marca.
    """
    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

    doc = fitz.open(str(pdf_path))

    texto1 = "  Emitido via"
    texto2 = "SGU Express"

    for page_index, page in enumerate(doc):
        width, height = page.rect.width, page.rect.height
        rotacao = page.rotation  # 0 para portrait, 90 para landscape

        print(f"[DEBUG] Página {page_index} – width={width}, height={height}, rotation={rotacao}")

        if rotacao == 90:
            x = 26
            y = 75
            angle = 90
            page.insert_text(
                (x, y),
                texto1,
                fontsize=9,
                color=(0.5, 0.5, 0.5),
                rotate=angle,
                overlay=True,
            )
            page.insert_text(
                (x + 10, y),
                texto2,
                fontsize=9,
                color=(0.5, 0.5, 0.5),
                rotate=angle,
                overlay=True,
            )

        else:
            x = width - 75
            y = 25
            angle = 0
            page.insert_text(
                (x, y),
                texto1,
                fontsize=9,
                color=(0.5, 0.5, 0.5),
                rotate=angle,
                overlay=True,
            )
            page.insert_text(
                (x, y + 11),
                texto2,
                fontsize=9,
                color=(0.5, 0.5, 0.5),
                rotate=angle,
                overlay=True,
            )

    out_path = pdf_path.with_name(pdf_path.stem + "_marca.pdf")
    doc.save(str(out_path))
    doc.close()

    print(f"Marca d'água aplicada com sucesso: {out_path}")
    return str(out_path)


def rasterizar_pdf(pdf_path: str, dpi: int = 150) -> str:
    """
    Recebe um PDF (tipicamente já com marca) e gera:
        <base>_final.pdf
    Rasterizado (imagem por página), para ficar não editável.
    Retorna o caminho do PDF final.
    """
    pdf_path = Path(pdf_path).resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    new_doc = fitz.open()

    for page_index, page in enumerate(doc):
        rect = page.rect
        pix = page.get_pixmap(dpi=dpi, alpha=False)

        new_page = new_doc.new_page(width=rect.width, height=rect.height)
        new_page.insert_image(rect, pixmap=pix)

    stem_base = pdf_path.stem
    if stem_base.endswith("_marca"):
        stem_base = stem_base[:-6]

    out_path = pdf_path.with_name(stem_base + "_final.pdf")

    new_doc.save(str(out_path), deflate=True)
    new_doc.close()
    doc.close()

    print(f"PDF rasterizado (não editável) gerado: {out_path}")
    return str(out_path)


def gerar_pdf_com_marca(xlsx_path: str) -> str:
    """
    Converte um .xlsx em PDF e aplica marca d'água.
    Retorna o caminho do PDF com marca (pode ter múltiplas páginas).
    """
    # 1) converter para PDF
    pdf_base = xlsx_to_pdf(xlsx_path)

    # 2) aplicar marca d’água (novo arquivo)
    pdf_marca = aplicar_marca_dagua_fitz(pdf_base)

    return pdf_marca


def gerar_pdf_final(xlsx_path: str) -> str:
    """
    Converte XLSX em PDF, mantém apenas a primeira página,
    aplica marca d'água e gera um PDF final rasterizado/imutável.

    Fluxo de arquivos:
        <nome>.pdf
        <nome>_1pag.pdf
        <nome>_1pag_marca.pdf
        <nome>_1pag_final.pdf

    Retorna o caminho FINAL (<nome>_1pag_final.pdf).
    """
    # 1) Converter XLSX → PDF
    pdf_base = xlsx_to_pdf(xlsx_path)

    # 2) Manter apenas a primeira página
    pdf_1pag = manter_apenas_primeira_pagina(pdf_base)

    # 3) Aplicar marca d'água
    pdf_marca = aplicar_marca_dagua_fitz(pdf_1pag)

    # 4) Rasterizar, deixando imutável
    pdf_final = rasterizar_pdf(pdf_marca, dpi=150)

    return pdf_final


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    xlsx_files = list(base_dir.glob("*.xlsx"))

    if not xlsx_files:
        print("Nenhum arquivo .xlsx encontrado na mesma pasta do script.")
    else:
        print(f"Encontrados {len(xlsx_files)} arquivo(s) .xlsx:")
        for f in xlsx_files:
            print(" -", f.name)

        print("\nIniciando conversão para PDF + marca d'água + corte para 1 página + raster...\n")

        for f in xlsx_files:
            try:
                pdf_final = gerar_pdf_final(str(f))
                print(f"[OK] PDF final gerado: {Path(pdf_final).name}\n")
            except Exception as e:
                print(f"[FALHA] {f.name}: {e}\n")
