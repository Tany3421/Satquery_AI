import os
import sys
import shutil
import docx

# Ensure current directory is on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from report_styles import ReportStyleManager
from report_part1 import build_front_matter, build_chapters_1_to_7
from report_part2 import build_chapters_8_to_14
from report_part3 import build_chapters_15_to_21_and_refs

def compile_academic_report():
    print("===============================================================")
    print("       SATQUERY AI: COMPILING ACADEMIC PROJECT REPORT          ")
    print("===============================================================")
    
    doc = docx.Document()
    mgr = ReportStyleManager(doc)
    
    print("[1/5] Building Front Matter (Title Page, Certificate, Declaration, Abstract, TOC, Lists)...")
    build_front_matter(mgr)
    
    print("[2/5] Building Chapters 1 through 7 (Introduction, Lit Review, Problem, Arch, Tech Stack, UI, Gateway)...")
    build_chapters_1_to_7(mgr)
    
    print("[3/5] Building Chapters 8 through 14 (VLM Engine, Grounding, SAM 2.1, Fallback, Preprocessing, DB, Data Flow)...")
    build_chapters_8_to_14(mgr)
    
    print("[4/5] Building Chapters 15 through 21 & References (Installation, Testing, Trade-Offs, Security, Roadmap, Citations)...")
    build_chapters_15_to_21_and_refs(mgr)
    
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    output_docx = os.path.join(project_root, "SatQuery_AI_Academic_Project_Report.docx")
    output_pdf = os.path.join(project_root, "SatQuery_AI_Academic_Project_Report.pdf")
    
    print(f"[5/5] Saving DOCX document to: {output_docx}...")
    doc.save(output_docx)
    print(f"      DOCX successfully written ({os.path.getsize(output_docx):,} bytes).")
    
    # Export to PDF via Word COM automation
    print("      Exporting publication-grade PDF via Microsoft Word COM...")
    try:
        import win32com.client
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        wb = word.Documents.Open(output_docx)
        wb.SaveAs(output_pdf, FileFormat=17) # 17 = wdFormatPDF
        wb.Close()
        word.Quit()
        print(f"      PDF successfully generated ({os.path.getsize(output_pdf):,} bytes): {output_pdf}")
    except Exception as e:
        print(f"      Word COM export encountered an error: {e}")
        print("      Falling back to direct reportlab compilation if needed...")
        
    # Also replicate to backend/uploads for web accessibility
    uploads_dir = os.path.join(project_root, "backend", "uploads")
    if os.path.exists(uploads_dir):
        shutil.copy2(output_docx, os.path.join(uploads_dir, "SatQuery_AI_Academic_Project_Report.docx"))
        if os.path.exists(output_pdf):
            shutil.copy2(output_pdf, os.path.join(uploads_dir, "SatQuery_AI_Academic_Project_Report.pdf"))
        print(f"      Synchronized copies to: {uploads_dir}")
        
    print("===============================================================")
    print("                 COMPILATION COMPLETED!                        ")
    print(f"  Word File (.docx): {output_docx}")
    if os.path.exists(output_pdf):
        print(f"  PDF File (.pdf):   {output_pdf}")
    print("===============================================================")

if __name__ == "__main__":
    compile_academic_report()
