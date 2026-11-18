#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synthetic corpus generator for RAG testing.
Creates fake documents with planted facts, traps, and evaluation questions.
"""

import json
import os
import sys
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pptx import Presentation
from pptx.util import Inches as PptxInches, Pt as PptxPt
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from PIL import Image, ImageDraw, ImageFont

# Output folder
from aiq.config import CORPUS_DIR, QUESTIONS_FILE

OUTPUT_DIR = str(CORPUS_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Planted facts storage - will be used to generate eval questions
PLANTED_FACTS = {
    "EcoBuild": [],
    "Lumina": [],
    "TechNova": []
}

# Track all generated files
GENERATED_FILES = []


def add_fact(client, fact_text, source_file, location, trap_type=None):
    """Register a planted fact for later verification."""
    PLANTED_FACTS[client].append({
        "fact": fact_text,
        "source_file": source_file,
        "location": location,
        "trap_type": trap_type
    })


# ====================
# DOCX GENERATORS
# ====================

def create_ecobuild_monthly_report():
    """EcoBuild - Monthly sustainability report (Romanian)"""
    filename = "2026-10-raport-lunar-ecobuild.docx"
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = Document()

    # Title
    title = doc.add_heading('Raport Lunar Octombrie 2026', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Heading 1
    doc.add_heading('1. Rezumat Executiv', 1)

    p1 = doc.add_paragraph(
        "În luna octombrie 2026, proiectul EcoVillage a înregistrat progrese semnificative în "
        "implementarea soluțiilor de construcție durabilă. Echipa noastră a finalizat instalarea "
        "panourilor solare pe 45 de unități rezidențiale, depășind ținta lunară cu 12%. "
    )
    add_fact("EcoBuild", "45 de unități rezidențiale", filename, "paragraph in section 1")

    p2 = doc.add_paragraph(
        "Bugetul lunar alocat pentru octombrie este de 125.000 EUR, cu o rată de execuție de 94%. "
        "Șeful de proiect Adrian Dumitru a aprobat extinderea fazei 2 până la 15 decembrie 2026. "
        "Conform instrucțiunilor interne, nu folosim niciodată termeni precum 'ieftin' sau 'reducere' "
        "în comunicarea cu clienții - ne concentrăm pe valoarea pe termen lung și sustenabilitate."
    )
    add_fact("EcoBuild", "125.000 EUR", filename, "paragraph in section 1", trap_type="collision_budget")
    add_fact("EcoBuild", "Adrian Dumitru", filename, "paragraph in section 1")
    add_fact("EcoBuild", "15 decembrie 2026", filename, "paragraph in section 1", trap_type="collision_deadline")
    add_fact("EcoBuild", "nu folosim niciodată termeni precum 'ieftin' sau 'reducere'", filename, "paragraph in section 1")

    # Heading 2
    doc.add_heading('2. Indicatori de Performanță', 1)
    doc.add_heading('2.1 Eficiență Energetică', 2)

    p3 = doc.add_paragraph(
        "Sistemele instalate în octombrie au generat o economie energetică de 38% comparativ cu "
        "standardele convenționale. Certificarea BREEAM Excellent a fost obținută pentru blocul A, "
        "marcând prima realizare de acest tip în portofoliul nostru românesc."
    )
    add_fact("EcoBuild", "economie energetică de 38%", filename, "section 2.1")

    # Table
    doc.add_heading('2.2 Progres pe Faze', 2)
    table = doc.add_table(rows=4, cols=3)
    table.style = 'Light Grid Accent 1'

    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Fază'
    hdr_cells[1].text = 'Status'
    hdr_cells[2].text = 'Procent Finalizat'

    table.rows[1].cells[0].text = 'Faza 1 - Fundații'
    table.rows[1].cells[1].text = 'Finalizat'
    table.rows[1].cells[2].text = '100%'

    table.rows[2].cells[0].text = 'Faza 2 - Structură'
    table.rows[2].cells[1].text = 'În desfășurare'
    table.rows[2].cells[2].text = '67%'

    table.rows[3].cells[0].text = 'Faza 3 - Finisaje verzi'
    table.rows[3].cells[1].text = 'Planificat'
    table.rows[3].cells[2].text = '0%'

    add_fact("EcoBuild", "67%", filename, "table in section 2.2")

    # Heading 3
    doc.add_heading('3. Provocări și Soluții', 1)
    doc.add_heading('3.1 Aprovizionare Materiale', 2)

    long_para = (
        "Pe parcursul lunii octombrie, am întâmpinat dificultăți semnificative în aprovizionarea cu "
        "materiale ecologice certificate, în special în cazul lemnului FSC și al betonului cu conținut "
        "redus de carbon. Furnizorul principal, GreenMat Solutions SRL, a raportat întârzieri de până "
        "la 3 săptămâni din cauza problemelor logistice la nivel european. Pentru a mitiga impactul, "
        "am identificat doi furnizori alternativi: EcoSupply International din Germania și Sustainable "
        "Build Materials din Polonia. Ambii furnizori au fost auditați și certificați conform "
        "standardelor noastre interne de calitate. Costurile suplimentare estimate pentru schimbarea "
        "furnizorilor sunt de aproximativ 8.500 EUR, reprezentând o creștere de 2,3% față de bugetul "
        "inițial alocat acestei categorii. Cu toate acestea, considerăm că această investiție este "
        "justificată pentru a menține calendarul proiectului și pentru a asigura calitatea materialelor. "
        "În plus, am negociat termeni preferențiali pentru comenzile viitoare, ceea ce va compensa "
        "parțial aceste costuri adiționale în trimestrul următor. Echipa de procurement condusă de "
        "ing. Maria Constantinescu a implementat un sistem de monitorizare în timp real a stocurilor, "
        "care va preveni astfel de situații în viitor și va optimiza fluxul de aprovizionare pentru "
        "următoarele 6 luni ale proiectului. Această soluție digitală integrează date de la toți "
        "furnizorii activi și generează alerte automate când nivelurile de stoc scad sub pragurile "
        "critice stabilite pentru fiecare categorie de materiale. Implementarea acestui sistem a "
        "necesitat o investiție de 12.000 EUR în software și training, dar proiecțiile indică economii "
        "de peste 45.000 EUR pe durata completă a proiectului prin reducerea timpilor de nefuncționare "
        "și optimizarea comenzilor. În concluzie, deși octombrie a prezentat provocări operaționale "
        "semnificative, măsurile corective implementate ne poziționează favorabil pentru atingerea "
        "obiectivelor trimestriale și anuale stabilite în planul strategic al proiectului EcoVillage. "
        "Următoarea revizuire a fost programată pentru 5 noiembrie 2026, când vom evalua eficacitatea "
        "noilor proceduri de aprovizionare și vom ajusta strategia dacă este necesar."
    )
    doc.add_paragraph(long_para)
    add_fact("EcoBuild", "ing. Maria Constantinescu", filename, "long paragraph in section 3.1")

    doc.save(filepath)
    GENERATED_FILES.append(filename)
    print(f"✓ Created {filename}")


def create_lumina_campaign_brief():
    """Lumina - Campaign brief (English)"""
    filename = "2026-11-brief-campanie-lumina.docx"
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = Document()

    # Title
    title = doc.add_heading('Winter Glow Campaign Brief', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading('1. Campaign Overview', 1)

    p1 = doc.add_paragraph(
        "The Winter Glow campaign for Lumina's new skincare line launches on December 1, 2026, "
        "targeting millennial and Gen-Z consumers across digital channels. The campaign budget is "
        "set at 85.000 EUR for the initial 6-week phase, with performance gates determining the "
        "rollout to additional markets."
    )
    add_fact("Lumina", "December 1, 2026", filename, "section 1", trap_type="collision_launch_date")
    add_fact("Lumina", "85.000 EUR", filename, "section 1", trap_type="collision_budget")

    doc.add_heading('2. Target Audience', 1)
    doc.add_heading('2.1 Primary Segment', 2)

    p2 = doc.add_paragraph(
        "Women aged 25-34, urban professionals with household income above 45.000 EUR annually. "
        "This segment represents 62% of our target reach. Creative director Sarah Mitchell has "
        "approved all visual assets with the requirement that we never use medical claims or "
        "before/after comparisons without clinical validation."
    )
    add_fact("Lumina", "62%", filename, "section 2.1")
    add_fact("Lumina", "Sarah Mitchell", filename, "section 2.1")
    add_fact("Lumina", "never use medical claims or before/after comparisons without clinical validation", filename, "section 2.1")

    doc.add_heading('2.2 Channel Strategy', 2)

    # Table
    table = doc.add_table(rows=5, cols=3)
    table.style = 'Light List Accent 1'

    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Channel'
    hdr_cells[1].text = 'Budget Allocation'
    hdr_cells[2].text = 'KPI Target'

    table.rows[1].cells[0].text = 'Instagram/TikTok'
    table.rows[1].cells[1].text = '45%'
    table.rows[1].cells[2].text = '2.5M impressions'

    table.rows[2].cells[0].text = 'YouTube Pre-roll'
    table.rows[2].cells[1].text = '25%'
    table.rows[2].cells[2].text = '800K views'

    table.rows[3].cells[0].text = 'Display Network'
    table.rows[3].cells[1].text = '20%'
    table.rows[3].cells[2].text = '1.2M impressions'

    table.rows[4].cells[0].text = 'Influencer Partnerships'
    table.rows[4].cells[1].text = '10%'
    table.rows[4].cells[2].text = '15 partnerships'

    add_fact("Lumina", "15 partnerships", filename, "table in section 2.2")

    doc.add_heading('3. Creative Guidelines', 1)

    long_para = (
        "The creative execution for the Winter Glow campaign must adhere to Lumina's comprehensive "
        "brand guidelines while introducing a fresh, seasonal aesthetic that resonates with our "
        "target demographic. All visual content should feature the signature Lumina color palette: "
        "soft rose (#F4E4E4), warm gold (#D4AF37), and winter white (#FAFAFA) as primary colors, "
        "with deep plum (#4A1942) as an accent for calls-to-action. Photography style requires "
        "natural lighting scenarios that emphasize the authentic, everyday beauty philosophy central "
        "to our brand positioning. Models should reflect genuine diversity in skin tones, ages within "
        "our target range, and lifestyle contexts. The mandated disclaimer for all paid media is: "
        "'Results may vary. Not tested on animals. Dermatologically approved for sensitive skin.' "
        "This exact wording was approved by our legal team on October 15, 2026, and cannot be "
        "modified without explicit written approval from General Counsel. Video content should be "
        "optimized for mobile-first viewing with subtitles in both English and Romanian, as our "
        "analytics indicate that 78% of our audience watches with sound off. The maximum video "
        "length for social platforms is 30 seconds, while YouTube pre-roll can extend to 15 seconds "
        "for non-skippable placements. Each piece of content must include our sustainability message "
        "highlighting the recycled packaging initiative, as this tested strongly in focus groups "
        "with a 91% positive response rate. Influencer content requires pre-approval 72 hours before "
        "posting, with review conducted by both the brand team and our compliance officer, Diana "
        "Popescu, who has final authority on all public-facing communications. The hashtag strategy "
        "centers on #WinterGlowLumina as the primary branded hashtag, supported by #SkincareRoutine, "
        "#NaturalBeauty, and #SustainableBeauty for broader discoverability. Analytics tracking must "
        "capture engagement rates, click-through rates, conversion rates, and sentiment analysis "
        "across all platforms, with daily reporting to the campaign dashboard accessible to all "
        "stakeholders. Any creative that deviates from these guidelines requires escalation to the "
        "Creative Review Board, which convenes every Wednesday at 14:00 CET for expedited approvals "
        "during the campaign flight period from December 1, 2026 through January 15, 2027."
    )
    doc.add_paragraph(long_para)
    add_fact("Lumina", "Diana Popescu", filename, "long paragraph in section 3")
    add_fact("Lumina", "78%", filename, "long paragraph in section 3")

    doc.save(filepath)
    GENERATED_FILES.append(filename)
    print(f"✓ Created {filename}")


def create_technova_status_report():
    """TechNova - Monthly status report (Mixed Romanian/English)"""
    filename = "2026-10-status-report-technova.docx"
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = Document()

    title = doc.add_heading('TechNova CloudSync - Status Report October 2026', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading('1. Executive Summary / Rezumat Executiv', 1)

    p1 = doc.add_paragraph(
        "October 2026 marked significant progress in the CloudSync platform development. The team "
        "delivered 23 story points across three sprints, achieving 94% of planned velocity. "
        "Monthly operational budget stands at 95.000 EUR with 89% utilization rate."
    )
    add_fact("TechNova", "95.000 EUR", filename, "section 1", trap_type="collision_budget")
    add_fact("TechNova", "23 story points", filename, "section 1")

    p2 = doc.add_paragraph(
        "Product Owner Marcus Chen a aprobat roadmap-ul pentru Q1 2027, cu focus pe integrarea "
        "API-urilor enterprise și îmbunătățirea performanței pentru date-seturi mari. Lansarea "
        "versiunii 2.5 este programată pentru 20 decembrie 2026."
    )
    add_fact("TechNova", "Marcus Chen", filename, "section 1")
    add_fact("TechNova", "20 decembrie 2026", filename, "section 1", trap_type="collision_deadline")

    doc.add_heading('2. Development Metrics', 1)

    # Table
    table = doc.add_table(rows=5, cols=3)
    table.style = 'Medium Grid 1 Accent 1'

    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Metric'
    hdr_cells[1].text = 'Target'
    hdr_cells[2].text = 'Actual'

    table.rows[1].cells[0].text = 'Code Coverage'
    table.rows[1].cells[1].text = '85%'
    table.rows[1].cells[2].text = '87%'

    table.rows[2].cells[0].text = 'API Response Time'
    table.rows[2].cells[1].text = '<200ms'
    table.rows[2].cells[2].text = '178ms'

    table.rows[3].cells[0].text = 'Uptime SLA'
    table.rows[3].cells[1].text = '99.9%'
    table.rows[3].cells[2].text = '99.94%'

    table.rows[4].cells[0].text = 'Customer Satisfaction'
    table.rows[4].cells[1].text = '4.5/5'
    table.rows[4].cells[2].text = '4.7/5'

    add_fact("TechNova", "87%", filename, "table in section 2")
    add_fact("TechNova", "99.94%", filename, "table in section 2")

    doc.add_heading('3. Arhitectură și Scalabilitate', 1)

    p3 = doc.add_paragraph(
        "The platform currently supports 12.500 active enterprise users with peak concurrent "
        "connections of 3.400 users. Conform ghidurilor interne de comunicare, niciodată nu "
        "promitem SLA-uri specifice clienților noi fără aprobarea echipei de infrastructure. "
        "Database optimization reduced query times by 34% compared to September baseline."
    )
    add_fact("TechNova", "12.500 active enterprise users", filename, "section 3")
    add_fact("TechNova", "niciodată nu promitem SLA-uri specifice clienților noi fără aprobarea echipei de infrastructure", filename, "section 3")

    doc.save(filepath)
    GENERATED_FILES.append(filename)
    print(f"✓ Created {filename}")


def create_ecobuild_meeting_notes():
    """EcoBuild - Meeting notes (Romanian)"""
    filename = "2026-11-meeting-notes-ecobuild.docx"
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = Document()

    title = doc.add_heading('Note de Întâlnire - Revizuire Proiect EcoVillage', 0)

    doc.add_paragraph('Data: 8 noiembrie 2026')
    doc.add_paragraph('Participanți: Adrian Dumitru, Maria Constantinescu, echipa tehnică')

    doc.add_heading('1. Actualizare Buget', 1)

    p1 = doc.add_paragraph(
        "IMPORTANT UPDATE: Bugetul lunar pentru noiembrie a fost revizuit și aprobat la 142.000 EUR "
        "(creștere față de 125.000 EUR anterior) pentru a acoperi costurile suplimentare cu "
        "furnizorii alternativi și sistemul nou de monitorizare. Această modificare este efectivă "
        "începând cu 1 noiembrie 2026."
    )
    add_fact("EcoBuild", "142.000 EUR", filename, "section 1", trap_type="superseded_fact_new")

    doc.add_heading('2. Milestone-uri', 1)

    p2 = doc.add_paragraph(
        "- Instalare panouri solare finalizată: 45 unități (target atins 112%)\n"
        "- Certificare BREEAM Excellent obținută pentru blocul A\n"
        "- Sistem monitorizare stocuri operațional din 5 noiembrie\n"
        "- Următoarea revizuire: 20 noiembrie 2026"
    )

    doc.save(filepath)
    GENERATED_FILES.append(filename)
    print(f"✓ Created {filename}")


def create_lumina_seo_strategy():
    """Lumina - SEO Strategy document (Romanian)"""
    filename = "2026-09-strategie-seo-lumina.docx"
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = Document()

    title = doc.add_heading('Strategie SEO - Lumina Skincare', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading('1. Obiective SEO', 1)

    p1 = doc.add_paragraph(
        "Strategia SEO pentru al patrulea trimestru 2026 vizează creșterea traficului organic "
        "cu 45% și îmbunătățirea rankingului pentru 25 de cuvinte cheie prioritare. Coordonatorul "
        "SEO Laura Ionescu a stabilit ca țintă primară atingerea poziției top 3 pentru 'îngrijire "
        "piele naturală' și 'cosmetice sustenabile România'."
    )
    add_fact("Lumina", "Laura Ionescu", filename, "section 1")
    add_fact("Lumina", "45%", filename, "section 1")

    doc.add_heading('2. Cuvinte Cheie Țintă', 1)
    doc.add_heading('2.1 Prioritate Înaltă', 2)

    # Long paragraph with facts
    long_para = (
        "Analiza competitivă realizată în august 2026 a identificat oportunități semnificative "
        "în segmentul de căutare informațională legat de rutine de îngrijire a pielii pentru "
        "sezonul rece. Volumul de căutări pentru 'hidratare piele iarna' a crescut cu 156% "
        "comparativ cu aceeași perioadă a anului trecut, indicând un interes crescut al consumatorilor "
        "pentru soluții specifice sezonului. Strategia noastră de conținut se concentrează pe crearea "
        "de articole educaționale aprofundate, cu lungime optimă între 1.800 și 2.500 de cuvinte, "
        "care să abordeze nevoile specifice ale publicului țintă. Fiecare articol trebuie să includă "
        "minimum 3 linkuri interne către pagini de produs relevante, dar fără a adopta un ton "
        "agresiv de vânzare. Conform ghidului nostru editorial aprobat de Sarah Mitchell, conținutul "
        "trebuie să fie în primul rând util și educațional, cu call-to-action-uri subtile integrate "
        "natural în flux. Planul de publicare prevede 12 articole noi pe lună, fiecare optimizat "
        "pentru un cluster de cuvinte cheie secundare care susțin termenii primari. Linkbuilding-ul "
        "se va concentra pe colaborări cu bloguri de lifestyle și publicații online cu autoritate "
        "de domeniu peste 40, evitând strictul site-uri de tip directory sau schimburi reciproce "
        "care ar putea afecta negativ profilul de link-uri. Ținta pentru trimestrul 4 este "
        "achiziționarea a minimum 35 de backlink-uri de calitate din surse relevante tematic. "
        "Monitorizarea performanței se realizează săptămânal prin Google Search Console și SEMrush, "
        "cu raportare lunară către Sarah Mitchell și echipa de marketing. Orice ajustare a strategiei "
        "necesită validare în ședințele bi-săptămânale de optimizare care au loc în fiecare joi "
        "la ora 10:00. Bugetul alocat pentru content creation și link acquisition este de 18.500 EUR "
        "lunar, cu posibilitatea de realocare între tactici în funcție de performanță. Meta descrierile "
        "trebuie să fie între 150-160 caractere și să includă întotdeauna un beneficiu clar pentru "
        "utilizator, evitând keyword stuffing sau promisiuni exagerate care ar putea reduce "
        "credibilitatea brandului."
    )
    doc.add_paragraph(long_para)
    add_fact("Lumina", "156%", filename, "long paragraph in section 2.1")
    add_fact("Lumina", "minimum 35 de backlink-uri", filename, "long paragraph in section 2.1")

    doc.save(filepath)
    GENERATED_FILES.append(filename)
    print(f"✓ Created {filename}")


# ====================
# PPTX GENERATORS
# ====================

def create_technova_pitch_deck():
    """TechNova - Investor pitch deck (English)"""
    filename = "2026-11-pitch-deck-technova.pptx"
    filepath = os.path.join(OUTPUT_DIR, filename)

    prs = Presentation()
    prs.slide_width = PptxInches(10)
    prs.slide_height = PptxInches(7.5)

    # Slide 1: Title
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "TechNova CloudSync Platform"
    subtitle.text = "Enterprise Data Synchronization Solution\nNovember 2026"

    # Slide 2: Market Opportunity
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Market Opportunity"

    tf = slide.shapes.placeholders[1].text_frame
    tf.text = "Total Addressable Market: $12.4B by 2027"
    p = tf.add_paragraph()
    p.text = "Current enterprise clients: 847 companies"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Annual Recurring Revenue: $23.5M"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Year-over-year growth: 187%"
    p.level = 1

    add_fact("TechNova", "847 companies", filename, "slide 2")
    add_fact("TechNova", "187%", filename, "slide 2")

    # Slide 3: Product Features
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Core Product Features"

    tf = slide.shapes.placeholders[1].text_frame
    tf.text = "Real-time data synchronization across cloud platforms"
    p = tf.add_paragraph()
    p.text = "Support for AWS, Azure, Google Cloud"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "99.94% uptime SLA guarantee"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Enterprise-grade security with SOC2 Type II compliance"
    p.level = 1

    # Add speaker notes with hidden fact
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = (
        "Key messaging: Emphasize our unique conflict resolution algorithm that processes "
        "4.2 million transactions per second. Never mention competitor names directly in "
        "client presentations per our sales guidelines approved by Marcus Chen."
    )
    add_fact("TechNova", "4.2 million transactions per second", filename, "slide 3 speaker notes")

    # Slide 4: Team
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Leadership Team"

    tf = slide.shapes.placeholders[1].text_frame
    tf.text = "Marcus Chen - Product Owner & Co-Founder"
    p = tf.add_paragraph()
    p.text = "Former Engineering Lead at Salesforce, 15 years SaaS experience"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Dr. Elena Popa - Chief Technology Officer"
    p.level = 0
    p = tf.add_paragraph()
    p.text = "PhD in Distributed Systems, ex-Google Cloud architect"
    p.level = 1

    add_fact("TechNova", "Dr. Elena Popa", filename, "slide 4")

    # Slide 5: Financial Projections
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title = slide.shapes.title
    title.text = "Financial Projections 2027"

    # Add table
    rows, cols = 4, 3
    left = PptxInches(1.5)
    top = PptxInches(2.5)
    width = PptxInches(7)
    height = PptxInches(3)

    table = slide.shapes.add_table(rows, cols, left, top, width, height).table

    table.cell(0, 0).text = "Quarter"
    table.cell(0, 1).text = "Revenue"
    table.cell(0, 2).text = "New Clients"

    table.cell(1, 0).text = "Q1 2027"
    table.cell(1, 1).text = "$6.8M"
    table.cell(1, 2).text = "120"

    table.cell(2, 0).text = "Q2 2027"
    table.cell(2, 1).text = "$8.2M"
    table.cell(2, 2).text = "145"

    table.cell(3, 0).text = "Q3 2027"
    table.cell(3, 1).text = "$9.5M"
    table.cell(3, 2).text = "165"

    # Slide 6-10: Additional content slides
    for i in range(6, 11):
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        title.text = f"Strategic Initiative {i-5}"

        tf = slide.shapes.placeholders[1].text_frame
        tf.text = f"Expansion into {['EMEA', 'APAC', 'LATAM', 'Government', 'Healthcare'][i-6]} sector"
        p = tf.add_paragraph()
        p.text = "Leveraging proven platform capabilities"
        p.level = 1

    prs.save(filepath)
    GENERATED_FILES.append(filename)
    print(f"✓ Created {filename}")


def create_ecobuild_presentation():
    """EcoBuild - Sustainability presentation (Romanian)"""
    filename = "2026-09-prezentare-sustenabilitate-ecobuild.pptx"
    filepath = os.path.join(OUTPUT_DIR, filename)

    prs = Presentation()

    # Slide 1: Title
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "EcoVillage - Construcții Sustenabile"
    subtitle.text = "Prezentare Tehnică Septembrie 2026"

    # Slide 2: Viziune
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Viziunea Proiectului"

    tf = slide.shapes.placeholders[1].text_frame
    tf.text = "Primul complex rezidențial carbon-neutral din România"
    p = tf.add_paragraph()
    p.text = "125 unități rezidențiale cu certificare BREEAM"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Reducere de 73% a amprentei de carbon vs. construcții tradiționale"
    p.level = 1

    add_fact("EcoBuild", "73%", filename, "slide 2")

    # Slide 3-10: Technical details
    topics = [
        "Soluții Energetice",
        "Materiale Ecologice",
        "Managementul Apei",
        "Biodiversitate",
        "Calitatea Aerului Interior",
        "Infrastructură Verde",
        "Timeline Implementare",
        "Echipa Proiectului"
    ]

    for i, topic in enumerate(topics, start=3):
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        title.text = topic

        tf = slide.shapes.placeholders[1].text_frame
        tf.text = f"Detalii tehnice pentru {topic.lower()}"
        p = tf.add_paragraph()
        p.text = "Implementare conform standardelor internaționale"
        p.level = 1

    # Slide 11: Contact
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Contact"

    tf = slide.shapes.placeholders[1].text_frame
    tf.text = "Adrian Dumitru - Șef Proiect"
    p = tf.add_paragraph()
    p.text = "adrian.dumitru@ecobuild.ro"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Maria Constantinescu - Procurement Lead"
    p.level = 0
    p = tf.add_paragraph()
    p.text = "maria.c@ecobuild.ro"
    p.level = 1

    prs.save(filepath)
    GENERATED_FILES.append(filename)
    print(f"✓ Created {filename}")


def create_lumina_brand_guidelines():
    """Lumina - Brand guidelines presentation (Mixed RO/EN)"""
    filename = "2026-10-brand-guidelines-lumina.pptx"
    filepath = os.path.join(OUTPUT_DIR, filename)

    prs = Presentation()

    # Slide 1
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "Lumina Brand Guidelines"
    subtitle.text = "Ghid de Identitate Vizuală | October 2026"

    # Slide 2
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Brand Essence / Esența Brandului"

    tf = slide.shapes.placeholders[1].text_frame
    tf.text = "Authentic beauty through sustainable innovation"
    p = tf.add_paragraph()
    p.text = "Frumusețe autentică prin inovație sustenabilă"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Target: Women 25-34, premium natural skincare"
    p.level = 1

    # Slide 3
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Color Palette"

    tf = slide.shapes.placeholders[1].text_frame
    tf.text = "Primary Colors:"
    p = tf.add_paragraph()
    p.text = "Soft Rose #F4E4E4"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Warm Gold #D4AF37"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Winter White #FAFAFA"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Accent: Deep Plum #4A1942"
    p.level = 1

    # Slide 4-12: More guidelines
    for i in range(4, 13):
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        topics = ["Typography", "Photography Style", "Logo Usage", "Tone of Voice",
                  "Social Media", "Packaging", "Retail Experience", "Digital Assets", "Dos and Don'ts"]
        title.text = topics[i-4] if i-4 < len(topics) else f"Section {i}"

        tf = slide.shapes.placeholders[1].text_frame
        tf.text = f"Guidelines for {topics[i-4] if i-4 < len(topics) else 'this section'}"

    prs.save(filepath)
    GENERATED_FILES.append(filename)
    print(f"✓ Created {filename}")


def create_lumina_media_plan():
    """Lumina - Media plan presentation (English)"""
    filename = "2026-11-media-plan-lumina.pptx"
    filepath = os.path.join(OUTPUT_DIR, filename)

    prs = Presentation()

    # Slide 1
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "Q4 2026 Media Plan"
    subtitle.text = "Lumina Winter Glow Campaign"

    # Slide 2
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = "Campaign Launch Details"

    tf = slide.shapes.placeholders[1].text_frame
    tf.text = "Launch Date: November 15, 2026"
    p = tf.add_paragraph()
    p.text = "Flight Duration: 8 weeks"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Total Media Budget: 92.000 EUR"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Target Reach: 3.2M unique users"
    p.level = 1

    add_fact("Lumina", "November 15, 2026", filename, "slide 2", trap_type="collision_launch_date")
    add_fact("Lumina", "92.000 EUR", filename, "slide 2", trap_type="collision_budget")

    # Slide 3: Channel Mix
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title = slide.shapes.title
    title.text = "Channel Investment Mix"

    # Add table
    rows, cols = 6, 3
    left = PptxInches(1)
    top = PptxInches(2)
    width = PptxInches(8)
    height = PptxInches(4)

    table = slide.shapes.add_table(rows, cols, left, top, width, height).table

    table.cell(0, 0).text = "Channel"
    table.cell(0, 1).text = "Investment"
    table.cell(0, 2).text = "Expected Reach"

    table.cell(1, 0).text = "Social Media"
    table.cell(1, 1).text = "€41,400"
    table.cell(1, 2).text = "2.1M"

    table.cell(2, 0).text = "Video Pre-roll"
    table.cell(2, 1).text = "€23,000"
    table.cell(2, 2).text = "850K"

    table.cell(3, 0).text = "Display"
    table.cell(3, 1).text = "€18,400"
    table.cell(3, 2).text = "1.5M"

    table.cell(4, 0).text = "Influencers"
    table.cell(4, 1).text = "€9,200"
    table.cell(4, 2).text = "650K"

    table.cell(5, 0).text = "TOTAL"
    table.cell(5, 1).text = "€92,000"
    table.cell(5, 2).text = "3.2M"

    # Slides 4-10
    for i in range(4, 11):
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        title.text = f"Week {i-3} Strategy"

        tf = slide.shapes.placeholders[1].text_frame
        tf.text = f"Tactical execution for week {i-3}"

    prs.save(filepath)
    GENERATED_FILES.append(filename)
    print(f"✓ Created {filename}")


# ====================
# PDF GENERATORS
# ====================

def create_technova_architecture_pdf():
    """TechNova - Technical architecture document (English, selectable text)"""
    filename = "2026-09-architecture-doc-technova.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=1  # Center
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=10
    )

    # Title
    story.append(Paragraph("TechNova CloudSync Platform", title_style))
    story.append(Paragraph("System Architecture Documentation", styles['Heading2']))
    story.append(Paragraph("Version 2.5 | September 2026", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # Section 1
    story.append(Paragraph("1. System Overview", heading1_style))
    story.append(Paragraph("1.1 Architecture Principles", heading2_style))

    text1 = (
        "CloudSync is built on a microservices architecture deployed across multiple availability "
        "zones to ensure high availability and fault tolerance. The system handles 12.500 active "
        "enterprise users with peak load capacity of 8.600 concurrent connections. Our infrastructure "
        "supports horizontal scaling with automatic provisioning based on demand patterns."
    )
    story.append(Paragraph(text1, styles['Normal']))
    story.append(Spacer(1, 0.3*cm))

    add_fact("TechNova", "8.600 concurrent connections", filename, "section 1.1")

    text2 = (
        "Chief Technology Officer Dr. Elena Popa oversees all architectural decisions with a focus "
        "on maintaining our 99.94% uptime commitment. System response times average 178ms across "
        "all API endpoints, significantly exceeding our SLA target of 200ms."
    )
    story.append(Paragraph(text2, styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # Section 2
    story.append(Paragraph("2. Core Components", heading1_style))
    story.append(Paragraph("2.1 Data Synchronization Engine", heading2_style))

    long_para = (
        "The synchronization engine represents the core innovation of the CloudSync platform, "
        "implementing a proprietary conflict resolution algorithm that processes 4.2 million "
        "transactions per second with sub-millisecond latency for most operations. This engine "
        "utilizes a distributed consensus protocol based on modified Raft algorithm, enhanced "
        "with our custom vector clock implementation to handle complex multi-cloud scenarios. "
        "The system maintains eventual consistency across all nodes while providing strong "
        "consistency guarantees for critical financial and healthcare data where regulatory "
        "compliance demands it. Data replication occurs in real-time with a maximum propagation "
        "delay of 45 milliseconds between geographically distributed data centers spanning three "
        "continents. Our monitoring infrastructure tracks over 2.400 distinct performance metrics "
        "continuously, feeding data into machine learning models that predict potential bottlenecks "
        "and automatically trigger scaling operations before degradation occurs. The platform "
        "integrates with all major cloud providers including AWS, Azure, and Google Cloud Platform, "
        "maintaining native API compatibility while abstracting infrastructure differences through "
        "our unified interface layer. Security implementation follows zero-trust principles with "
        "end-to-end encryption using AES-256 for data at rest and TLS 1.3 for data in transit. "
        "Access control leverages OAuth 2.0 with PKCE extension and supports SAML 2.0 for enterprise "
        "SSO integration. Compliance certifications include SOC 2 Type II, ISO 27001, GDPR, and "
        "HIPAA for healthcare customers. Per our internal guidelines established by Marcus Chen, "
        "we never commit to custom SLA terms without thorough infrastructure team review and capacity "
        "planning, as over-commitment has historically led to service degradation. Database layer "
        "uses PostgreSQL with Citus extension for horizontal sharding, complemented by Redis clusters "
        "for caching frequently accessed data and session management. Query optimization reduced "
        "average database response times by 34% in the recent release, with the slowest queries now "
        "completing under 50 milliseconds. Backup strategy implements continuous archiving with "
        "point-in-time recovery capability, maintaining 30 days of incremental backups and 365 days "
        "of monthly snapshots stored across geographically diverse locations with 99.999999999% "
        "durability guarantee."
    )
    story.append(Paragraph(long_para, styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    add_fact("TechNova", "2.400 distinct performance metrics", filename, "long paragraph in section 2.1")

    # Section 3 with table
    story.append(PageBreak())
    story.append(Paragraph("3. Performance Metrics", heading1_style))
    story.append(Paragraph("3.1 Current System Performance", heading2_style))
    story.append(Spacer(1, 0.3*cm))

    table_data = [
        ['Metric', 'Target', 'Current', 'Trend'],
        ['API Response Time', '<200ms', '178ms', '↓'],
        ['Uptime SLA', '99.9%', '99.94%', '→'],
        ['Error Rate', '<0.1%', '0.07%', '↓'],
        ['Throughput', '10K req/s', '12.3K req/s', '↑'],
        ['Data Sync Latency', '<100ms', '45ms', '↓']
    ]

    t = Table(table_data, colWidths=[4.5*cm, 3*cm, 3*cm, 2*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7'))
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    add_fact("TechNova", "12.3K req/s", filename, "table in section 3.1")

    # Build PDF
    doc.build(story)
    GENERATED_FILES.append(filename)
    print(f"✓ Created {filename}")


def create_lumina_campaign_report_pdf():
    """Lumina - Campaign report (Romanian, selectable text)"""
    filename = "2026-10-raport-campanie-lumina.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=20, spaceAfter=20, alignment=1)
    story.append(Paragraph("Raport Campanie Summer Radiance", title_style))
    story.append(Paragraph("Perioada: Iulie - August 2026", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # Section 1
    h1_style = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=14, spaceAfter=10)
    story.append(Paragraph("1. Rezultate Generale", h1_style))

    text1 = (
        "Campania Summer Radiance desfășurată în perioada iulie-august 2026 a generat rezultate "
        "peste așteptări pe toate canalele digitale. Investiția totală de 78.000 EUR a generat "
        "un ROI de 3.4x, cu vânzări directe atribuite de 265.000 EUR și o creștere a brand "
        "awareness de 52% în rândul grupului țintă."
    )
    story.append(Paragraph(text1, styles['Normal']))
    story.append(Spacer(1, 0.3*cm))

    add_fact("Lumina", "78.000 EUR", filename, "section 1")
    add_fact("Lumina", "52%", filename, "section 1")

    # Section 2
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, spaceAfter=8)
    story.append(Paragraph("2. Performanță pe Canale", h1_style))
    story.append(Paragraph("2.1 Social Media", h2_style))

    text2 = (
        "Instagram și TikTok au generat 4.2 milioane de impresii cu un engagement rate mediu de "
        "6.8%, depășind benchmark-ul industriei de 4.2%. Directorului creativ Sarah Mitchell a "
        "fost deosebit de mulțumită de performanța conținutului video short-form, care a acumulat "
        "peste 850.000 de vizualizări organice."
    )
    story.append(Paragraph(text2, styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    add_fact("Lumina", "6.8%", filename, "section 2.1")

    # Long paragraph
    story.append(Paragraph("2.2 Strategia de Conținut", h2_style))

    long_para = (
        "Strategia de conținut implementată pentru campania Summer Radiance s-a bazat pe cercetări "
        "extensive ale comportamentului consumatorilor din segmentul demografic 25-34 ani, cu focus "
        "particular pe preferințele legate de autenticitate și transparență în comunicarea brandurilor "
        "de cosmetice. Fiecare piesă de conținut a fost creată respectând cu strictețe ghidul de brand "
        "aprobat de Sarah Mitchell, care stipulează că niciodată nu folosim imagini supraprocesate sau "
        "filtre care denaturează rezultatele reale ale produselor noastre. Această abordare autentică "
        "a rezonat puternic cu audiența, generând un sentiment pozitiv în 89% din mențiunile brandului "
        "pe rețelele sociale, comparativ cu media industriei de 67%. Collaborarea cu 28 de micro-influenceri "
        "autentici, selectați pe criterii stricte de aliniere cu valorile brandului, a adus o rată de "
        "conversie de 8.2% din traficul generat, semnificativ peste ținta inițială de 5%. Fiecare "
        "influencer a primit un brief detaliat care sublinia importanța divulgării transparente a "
        "parteneriatului și a încurajării dialogului autentic cu follower-ii, evitând scripturile rigide "
        "care par neautentice. Analizele post-campanie au relevat că cele mai performante postări au "
        "fost cele care au integrat natural produsele în rutine zilnice reale, cu storytelling personal "
        "și vulnerabilitate, mai degrabă decât simple demonstrații de produs. Aceasta validează strategia "
        "noastră pe termen lung de a construi o comunitate angajată în jurul valorilor brandului, nu doar "
        "o audiență pasivă de consumatori. Investiția în conținut video de lungă durată pe YouTube a "
        "generat o rată de vizionare completă de 73%, indicând un nivel ridicat de interes și engagement "
        "cu mesajele noastre educaționale despre skincare. Diana Popescu din echipa de compliance a validat "
        "toate claim-urile de produs înainte de publicare, asigurând conformitatea cu reglementările "
        "europene privind produsele cosmetice și evitând orice risc legal sau reputațional. Această abordare "
        "meticuloasă, deși time-intensive, a prevenit orice incident care ar fi putut afecta negativ "
        "percepția brandului în timpul unei campanii cu vizibilitate ridicată."
    )
    story.append(Paragraph(long_para, styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    add_fact("Lumina", "89%", filename, "long paragraph in section 2.2")
    add_fact("Lumina", "28 de micro-influenceri", filename, "long paragraph in section 2.2")

    # Table
    story.append(PageBreak())
    story.append(Paragraph("3. Metrici Detaliate", h1_style))
    story.append(Spacer(1, 0.3*cm))

    table_data = [
        ['Canal', 'Investiție', 'Reach', 'Conversii'],
        ['Instagram/TikTok', '35.100 EUR', '2.8M', '1.247'],
        ['YouTube', '19.500 EUR', '1.2M', '683'],
        ['Display Ads', '15.600 EUR', '3.5M', '412'],
        ['Influencer', '7.800 EUR', '950K', '891'],
        ['TOTAL', '78.000 EUR', '8.45M', '3.233']
    ]

    t = Table(table_data, colWidths=[4*cm, 3.5*cm, 3*cm, 3*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D4AF37')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FAFAFA')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(t)

    doc.build(story)
    GENERATED_FILES.append(filename)
    print(f"✓ Created {filename}")


def create_ecobuild_contract_scanned_pdf():
    """EcoBuild - Scanned-style contract (Romanian, text as image)"""
    filename = "2026-11-contract-scan-ecobuild.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # Create images with text rendered as pixels
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    import io

    # We'll create a PDF with images of text
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    # Page 1
    img1 = Image.new('RGB', (2480, 3508), color='white')  # A4 at 300 DPI
    d1 = ImageDraw.Draw(img1)

    try:
        font_title = ImageFont.truetype("arial.ttf", 60)
        font_body = ImageFont.truetype("arial.ttf", 36)
        font_small = ImageFont.truetype("arial.ttf", 32)
    except:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Title
    d1.text((100, 100), "CONTRACT DE PRESTĂRI SERVICII", fill='black', font=font_title)
    d1.text((100, 200), "Nr. 2026/ECO/234", fill='black', font=font_body)
    d1.text((100, 280), "Data: 10 noiembrie 2026", fill='black', font=font_body)

    # Body text
    y_pos = 400
    text_lines = [
        "Între:",
        "",
        "EcoBuild Solutions SRL, cod fiscal RO12345678,",
        "reprezentată legal prin Adrian Dumitru - Director Proiect",
        "",
        "și",
        "",
        "GreenMat Solutions SRL, cod fiscal RO87654321",
        "",
        "Obiectul contractului:",
        "Furnizare materiale ecologice certificate pentru proiectul",
        "EcoVillage conform specificațiilor tehnice anexate.",
        "",
        "Valoarea contractului: 142.000 EUR",
        "Perioada de execuție: 1 noiembrie 2026 - 28 februarie 2027",
        "",
        "Termeni de plată: 30 zile de la livrare",
        "Garanție: 24 luni pentru toate materialele furnizate",
        "",
        "Clauze speciale:",
        "- Toate materialele trebuie să aibă certificare FSC",
        "- Livrările se fac conform graficului aprobat de ing. Maria",
        "  Constantinescu, responsabil procurement",
        "- Penalități de 0.5% pe zi pentru întârzieri",
    ]

    for line in text_lines:
        d1.text((100, y_pos), line, fill='black', font=font_body)
        y_pos += 50

    # Save page 1
    img1_buffer = io.BytesIO()
    img1.save(img1_buffer, format='PNG')
    img1_buffer.seek(0)

    temp_img1 = "temp_scan_page1.png"
    img1.save(temp_img1)
    c.drawImage(temp_img1, 0, 0, width=width, height=height)
    c.showPage()

    # Page 2
    img2 = Image.new('RGB', (2480, 3508), color='white')
    d2 = ImageDraw.Draw(img2)

    y_pos = 100
    text_lines_2 = [
        "Anexa 1 - Specificații Tehnice",
        "",
        "Materiale solicitate:",
        "",
        "1. Lemn FSC certificat - 450 m³",
        "2. Beton low-carbon - 1.200 m³",
        "3. Panouri solare - 45 unități (instalate deja)",
        "4. Materiale izolație ecologică - 2.500 m²",
        "",
        "Conformitatea cu standardele:",
        "- BREEAM Excellent (certificare obținută pentru blocul A)",
        "- Economie energetică minimă: 38%",
        "- Reducere amprenta carbon: 73% vs. construcții standard",
        "",
        "督督督督督督督督督督督督督督督督督",
        "",
        "Director Proiect                    Furnizor",
        "Adrian Dumitru                     GreenMat Solutions",
        "EcoBuild Solutions SRL",
        "",
        "Data: 10 noiembrie 2026",
    ]

    for line in text_lines_2:
        d2.text((100, y_pos), line, fill='black', font=font_body)
        y_pos += 50

    temp_img2 = "temp_scan_page2.png"
    img2.save(temp_img2)
    c.drawImage(temp_img2, 0, 0, width=width, height=height)

    c.save()

    # Clean up temp files
    try:
        os.remove(temp_img1)
        os.remove(temp_img2)
    except:
        pass

    add_fact("EcoBuild", "142.000 EUR", filename, "scanned page 1", trap_type="superseded_fact_new")

    GENERATED_FILES.append(filename)
    print(f"✓ Created {filename}")


# ====================
# XLSX GENERATOR
# ====================

def create_lumina_budget_xlsx():
    """Lumina - Budget tracking spreadsheet (Mixed RO/EN)"""
    filename = "2026-11-budget-tracking-lumina.xlsx"
    filepath = os.path.join(OUTPUT_DIR, filename)

    wb = Workbook()
    ws = wb.active
    ws.title = "Q4 2026 Budget"

    # Headers
    ws['A1'] = 'Lumina Marketing Budget - Q4 2026'
    ws['A1'].font = ws['A1'].font.copy(bold=True, size=14)

    ws['A3'] = 'Campaign / Campanie'
    ws['B3'] = 'Budget Allocated (EUR)'
    ws['C3'] = 'Spent (EUR)'
    ws['D3'] = 'Remaining (EUR)'
    ws['E3'] = 'Status'

    # Make headers bold
    for cell in ws[3]:
        if cell.value:
            cell.font = cell.font.copy(bold=True)

    # Data rows
    campaigns = [
        ['Summer Radiance (Jul-Aug)', 78000, 78000, 0, 'Closed'],
        ['Autumn Glow (Sep-Oct)', 67000, 65200, 1800, 'Closed'],
        ['Winter Glow (Nov-Dec)', 92000, 12400, 79600, 'Active'],
        ['SEO & Content', 18500, 16300, 2200, 'Ongoing'],
        ['Brand Partnerships', 25000, 22100, 2900, 'Ongoing'],
        ['Social Media Management', 15000, 14200, 800, 'Ongoing'],
    ]

    row = 4
    for campaign in campaigns:
        ws[f'A{row}'] = campaign[0]
        ws[f'B{row}'] = campaign[1]
        ws[f'C{row}'] = campaign[2]
        ws[f'D{row}'] = campaign[3]
        ws[f'E{row}'] = campaign[4]
        row += 1

    # Total row
    ws[f'A{row}'] = 'TOTAL Q4'
    ws[f'A{row}'].font = ws[f'A{row}'].font.copy(bold=True)
    ws[f'B{row}'] = sum(c[1] for c in campaigns)
    ws[f'B{row}'].font = ws[f'B{row}'].font.copy(bold=True)
    ws[f'C{row}'] = sum(c[2] for c in campaigns)
    ws[f'D{row}'] = sum(c[3] for c in campaigns)

    # Add approval info
    ws['A13'] = 'Approved by: Sarah Mitchell, Creative Director'
    ws['A14'] = 'Compliance review: Diana Popescu'
    ws['A15'] = 'Last updated: November 8, 2026'

    # Notes section
    ws['A17'] = 'Notes / Notițe:'
    ws['A17'].font = ws['A17'].font.copy(bold=True)
    ws['A18'] = '- Winter Glow campaign budget increased from initial 85.000 EUR'
    ws['A19'] = '- Launch date revised to November 15, 2026 (was December 1)'
    ws['A20'] = '- Total influencer partnerships target: 15 micro-influencers'
    ws['A21'] = '- All campaigns must comply with "no medical claims" policy'

    add_fact("Lumina", "92000", filename, "Excel cell B6")
    add_fact("Lumina", "295500", filename, "Excel total cell B10")

    # Adjust column widths
    ws.column_dimensions['A'].width = 35
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 18
    ws.column_dimensions['E'].width = 12

    wb.save(filepath)
    GENERATED_FILES.append(filename)
    print(f"✓ Created {filename}")


# ====================
# MAIN EXECUTION
# ====================

def generate_all_documents():
    """Generate all synthetic documents"""
    print("\n=== Generating Synthetic Corpus ===\n")

    print("Creating DOCX files...")
    create_ecobuild_monthly_report()
    create_lumina_campaign_brief()
    create_technova_status_report()
    create_ecobuild_meeting_notes()
    create_lumina_seo_strategy()

    print("\nCreating PPTX files...")
    create_technova_pitch_deck()
    create_ecobuild_presentation()
    create_lumina_brand_guidelines()
    create_lumina_media_plan()

    print("\nCreating PDF files...")
    create_technova_architecture_pdf()
    create_lumina_campaign_report_pdf()
    create_ecobuild_contract_scanned_pdf()

    print("\nCreating XLSX file...")
    create_lumina_budget_xlsx()

    print(f"\n=== Generation Complete ===")
    print(f"Total files created: {len(GENERATED_FILES)}")


def generate_eval_questions():
    """Generate evaluation questions based on planted facts"""
    print("\n=== Generating Evaluation Questions ===\n")

    questions = []
    qid = 1

    # EcoBuild questions
    questions.extend([
        {
            "id": f"Q{qid:03d}",
            "client": "EcoBuild",
            "question": "Câte unități rezidențiale au avut panourile solare instalate în octombrie 2026?",
            "expected_answer": "45 de unități rezidențiale",
            "source_file": "2026-10-raport-lunar-ecobuild.docx",
            "location": "paragraph in section 1",
            "trap_type": None
        },
        {
            "id": f"Q{qid+1:03d}",
            "client": "EcoBuild",
            "question": "What is EcoBuild's monthly budget for October 2026?",
            "expected_answer": "125.000 EUR (superseded by 142.000 EUR in November)",
            "source_file": "2026-10-raport-lunar-ecobuild.docx",
            "location": "paragraph in section 1",
            "trap_type": "superseded_fact_old"
        },
        {
            "id": f"Q{qid+2:03d}",
            "client": "EcoBuild",
            "question": "What is EcoBuild's current monthly budget as of November 2026?",
            "expected_answer": "142.000 EUR",
            "source_file": "2026-11-meeting-notes-ecobuild.docx",
            "location": "section 1",
            "trap_type": "superseded_fact_new"
        },
        {
            "id": f"Q{qid+3:03d}",
            "client": "EcoBuild",
            "question": "Cine este șeful de proiect pentru EcoVillage?",
            "expected_answer": "Adrian Dumitru",
            "source_file": "2026-10-raport-lunar-ecobuild.docx",
            "location": "paragraph in section 1",
            "trap_type": None
        },
        {
            "id": f"Q{qid+4:03d}",
            "client": "EcoBuild",
            "question": "Care este procentul de economie energetică obținut de sistemele instalate?",
            "expected_answer": "38%",
            "source_file": "2026-10-raport-lunar-ecobuild.docx",
            "location": "section 2.1",
            "trap_type": None
        },
        {
            "id": f"Q{qid+5:03d}",
            "client": "EcoBuild",
            "question": "What percentage is Phase 2 completed?",
            "expected_answer": "67%",
            "source_file": "2026-10-raport-lunar-ecobuild.docx",
            "location": "table in section 2.2",
            "trap_type": "table_fact"
        },
        {
            "id": f"Q{qid+6:03d}",
            "client": "EcoBuild",
            "question": "Care este reducerea amprentei de carbon comparativ cu construcțiile tradiționale?",
            "expected_answer": "73%",
            "source_file": "2026-09-prezentare-sustenabilitate-ecobuild.pptx",
            "location": "slide 2",
            "trap_type": None
        },
        {
            "id": f"Q{qid+7:03d}",
            "client": "EcoBuild",
            "question": "What is EcoBuild's policy on using discount language with clients?",
            "expected_answer": "nu folosim niciodată termeni precum 'ieftin' sau 'reducere'",
            "source_file": "2026-10-raport-lunar-ecobuild.docx",
            "location": "paragraph in section 1",
            "trap_type": None
        },
    ])
    qid += 8

    # Lumina questions
    questions.extend([
        {
            "id": f"Q{qid:03d}",
            "client": "Lumina",
            "question": "When does the Winter Glow campaign launch according to the brief?",
            "expected_answer": "December 1, 2026",
            "source_file": "2026-11-brief-campanie-lumina.docx",
            "location": "section 1",
            "trap_type": "collision_launch_date"
        },
        {
            "id": f"Q{qid+1:03d}",
            "client": "Lumina",
            "question": "What is the actual launch date for Winter Glow campaign per the media plan?",
            "expected_answer": "November 15, 2026",
            "source_file": "2026-11-media-plan-lumina.pptx",
            "location": "slide 2",
            "trap_type": "collision_launch_date"
        },
        {
            "id": f"Q{qid+2:03d}",
            "client": "Lumina",
            "question": "Care este bugetul campaniei Winter Glow menționat în brief?",
            "expected_answer": "85.000 EUR",
            "source_file": "2026-11-brief-campanie-lumina.docx",
            "location": "section 1",
            "trap_type": "collision_budget"
        },
        {
            "id": f"Q{qid+3:03d}",
            "client": "Lumina",
            "question": "What is the total media budget for Winter Glow in the media plan?",
            "expected_answer": "92.000 EUR",
            "source_file": "2026-11-media-plan-lumina.pptx",
            "location": "slide 2",
            "trap_type": "collision_budget"
        },
        {
            "id": f"Q{qid+4:03d}",
            "client": "Lumina",
            "question": "Who is Lumina's creative director?",
            "expected_answer": "Sarah Mitchell",
            "source_file": "2026-11-brief-campanie-lumina.docx",
            "location": "section 2.1",
            "trap_type": None
        },
        {
            "id": f"Q{qid+5:03d}",
            "client": "Lumina",
            "question": "Câte parteneriate cu influenceri sunt ținta pentru campanie?",
            "expected_answer": "15 partnerships",
            "source_file": "2026-11-brief-campanie-lumina.docx",
            "location": "table in section 2.2",
            "trap_type": "table_fact"
        },
        {
            "id": f"Q{qid+6:03d}",
            "client": "Lumina",
            "question": "What percentage of target audience watches with sound off?",
            "expected_answer": "78%",
            "source_file": "2026-11-brief-campanie-lumina.docx",
            "location": "long paragraph in section 3",
            "trap_type": None
        },
        {
            "id": f"Q{qid+7:03d}",
            "client": "Lumina",
            "question": "Cine are autoritate finală asupra comunicărilor publice la Lumina?",
            "expected_answer": "Diana Popescu, compliance officer",
            "source_file": "2026-11-brief-campanie-lumina.docx",
            "location": "long paragraph in section 3",
            "trap_type": None
        },
        {
            "id": f"Q{qid+8:03d}",
            "client": "Lumina",
            "question": "What is Lumina's policy on medical claims in advertising?",
            "expected_answer": "Never use medical claims or before/after comparisons without clinical validation",
            "source_file": "2026-11-brief-campanie-lumina.docx",
            "location": "section 2.1",
            "trap_type": None
        },
        {
            "id": f"Q{qid+9:03d}",
            "client": "Lumina",
            "question": "Care a fost ROI-ul campaniei Summer Radiance?",
            "expected_answer": "3.4x",
            "source_file": "2026-10-raport-campanie-lumina.pdf",
            "location": "section 1",
            "trap_type": None
        },
        {
            "id": f"Q{qid+10:03d}",
            "client": "Lumina",
            "question": "What was the engagement rate for social media in Summer Radiance?",
            "expected_answer": "6.8%",
            "source_file": "2026-10-raport-campanie-lumina.pdf",
            "location": "section 2.1",
            "trap_type": None
        },
        {
            "id": f"Q{qid+11:03d}",
            "client": "Lumina",
            "question": "Câți micro-influenceri au fost utilizați în Summer Radiance?",
            "expected_answer": "28 de micro-influenceri",
            "source_file": "2026-10-raport-campanie-lumina.pdf",
            "location": "long paragraph in section 2.2",
            "trap_type": None
        },
    ])
    qid += 12

    # TechNova questions
    questions.extend([
        {
            "id": f"Q{qid:03d}",
            "client": "TechNova",
            "question": "What is TechNova's monthly operational budget?",
            "expected_answer": "95.000 EUR",
            "source_file": "2026-10-status-report-technova.docx",
            "location": "section 1",
            "trap_type": "collision_budget"
        },
        {
            "id": f"Q{qid+1:03d}",
            "client": "TechNova",
            "question": "Când este programată lansarea versiunii 2.5?",
            "expected_answer": "20 decembrie 2026",
            "source_file": "2026-10-status-report-technova.docx",
            "location": "section 1",
            "trap_type": "collision_deadline"
        },
        {
            "id": f"Q{qid+2:03d}",
            "client": "TechNova",
            "question": "Who is TechNova's Product Owner?",
            "expected_answer": "Marcus Chen",
            "source_file": "2026-10-status-report-technova.docx",
            "location": "section 1",
            "trap_type": None
        },
        {
            "id": f"Q{qid+3:03d}",
            "client": "TechNova",
            "question": "What is the actual code coverage percentage achieved?",
            "expected_answer": "87%",
            "source_file": "2026-10-status-report-technova.docx",
            "location": "table in section 2",
            "trap_type": "table_fact"
        },
        {
            "id": f"Q{qid+4:03d}",
            "client": "TechNova",
            "question": "Care este uptime-ul actual al platformei?",
            "expected_answer": "99.94%",
            "source_file": "2026-10-status-report-technova.docx",
            "location": "table in section 2",
            "trap_type": None
        },
        {
            "id": f"Q{qid+5:03d}",
            "client": "TechNova",
            "question": "How many active enterprise users does the platform support?",
            "expected_answer": "12.500 active enterprise users",
            "source_file": "2026-10-status-report-technova.docx",
            "location": "section 3",
            "trap_type": None
        },
        {
            "id": f"Q{qid+6:03d}",
            "client": "TechNova",
            "question": "What is TechNova's policy on promising SLAs to new clients?",
            "expected_answer": "niciodată nu promitem SLA-uri specifice clienților noi fără aprobarea echipei de infrastructure",
            "source_file": "2026-10-status-report-technova.docx",
            "location": "section 3",
            "trap_type": None
        },
        {
            "id": f"Q{qid+7:03d}",
            "client": "TechNova",
            "question": "Câte companii client are în prezent TechNova?",
            "expected_answer": "847 companies",
            "source_file": "2026-11-pitch-deck-technova.pptx",
            "location": "slide 2",
            "trap_type": None
        },
        {
            "id": f"Q{qid+8:03d}",
            "client": "TechNova",
            "question": "What is the year-over-year growth rate?",
            "expected_answer": "187%",
            "source_file": "2026-11-pitch-deck-technova.pptx",
            "location": "slide 2",
            "trap_type": None
        },
        {
            "id": f"Q{qid+9:03d}",
            "client": "TechNova",
            "question": "How many transactions per second does the conflict resolution algorithm process?",
            "expected_answer": "4.2 million transactions per second",
            "source_file": "2026-11-pitch-deck-technova.pptx",
            "location": "slide 3 speaker notes",
            "trap_type": "speaker_notes_fact"
        },
        {
            "id": f"Q{qid+10:03d}",
            "client": "TechNova",
            "question": "Who is TechNova's Chief Technology Officer?",
            "expected_answer": "Dr. Elena Popa",
            "source_file": "2026-11-pitch-deck-technova.pptx",
            "location": "slide 4",
            "trap_type": None
        },
        {
            "id": f"Q{qid+11:03d}",
            "client": "TechNova",
            "question": "What is the peak concurrent connection capacity?",
            "expected_answer": "8.600 concurrent connections",
            "source_file": "2026-09-architecture-doc-technova.pdf",
            "location": "section 1.1",
            "trap_type": None
        },
    ])
    qid += 12

    # Cross-client collision questions
    questions.extend([
        {
            "id": f"Q{qid:03d}",
            "client": "ALL",
            "question": "What is the monthly budget for each client project?",
            "expected_answer": "EcoBuild: 142.000 EUR (Nov), Lumina: varies by campaign, TechNova: 95.000 EUR",
            "source_file": "multiple",
            "location": "various",
            "trap_type": "collision_test"
        },
        {
            "id": f"Q{qid+1:03d}",
            "client": "EcoBuild",
            "question": "What is the deadline for EcoBuild's Phase 2?",
            "expected_answer": "15 decembrie 2026",
            "source_file": "2026-10-raport-lunar-ecobuild.docx",
            "location": "paragraph in section 1",
            "trap_type": "collision_deadline"
        },
        {
            "id": f"Q{qid+2:03d}",
            "client": "TechNova",
            "question": "Care este deadline-ul pentru TechNova versiunea 2.5?",
            "expected_answer": "20 decembrie 2026",
            "source_file": "2026-10-status-report-technova.docx",
            "location": "section 1",
            "trap_type": "collision_deadline"
        },
    ])
    qid += 3

    # Unanswerable questions
    questions.extend([
        {
            "id": f"Q{qid:03d}",
            "client": "EcoBuild",
            "question": "What is the profit margin for the EcoVillage project?",
            "expected_answer": "NOT_IN_CORPUS",
            "source_file": None,
            "location": None,
            "trap_type": "unanswerable"
        },
        {
            "id": f"Q{qid+1:03d}",
            "client": "Lumina",
            "question": "Care este salariul mediu al echipei de marketing Lumina?",
            "expected_answer": "NOT_IN_CORPUS",
            "source_file": None,
            "location": None,
            "trap_type": "unanswerable"
        },
        {
            "id": f"Q{qid+2:03d}",
            "client": "TechNova",
            "question": "What programming languages is CloudSync built with?",
            "expected_answer": "NOT_IN_CORPUS",
            "source_file": None,
            "location": None,
            "trap_type": "unanswerable"
        },
        {
            "id": f"Q{qid+3:03d}",
            "client": "ALL",
            "question": "Which client has the highest customer satisfaction score?",
            "expected_answer": "NOT_IN_CORPUS",
            "source_file": None,
            "location": None,
            "trap_type": "unanswerable"
        },
    ])

    # Save to JSON
    eval_file = str(QUESTIONS_FILE)
    with open(eval_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"✓ Created {eval_file} with {len(questions)} questions")
    print(f"  - Questions with sources: {len([q for q in questions if q['source_file']])}")
    print(f"  - Unanswerable questions: {len([q for q in questions if q['trap_type'] == 'unanswerable'])}")
    print(f"  - Collision traps: {len([q for q in questions if 'collision' in str(q['trap_type'])])}")


if __name__ == "__main__":
    generate_all_documents()
    generate_eval_questions()
    print("\n✓ All synthetic corpus files generated successfully!")
    print(f"\nGenerated {len(GENERATED_FILES)} documents in {OUTPUT_DIR}/")
    print("\nNext step: Run verify_corpus.py to validate all planted facts")
