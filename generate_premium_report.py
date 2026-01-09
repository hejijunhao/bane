#!/usr/bin/env python3
"""
Premium Market Research Report Generator
Transforms the IoT Robotics Antenna Market Strategy report into a $10k-quality document
"""

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, ListFlowable, ListItem,
    Flowable, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO
import tempfile

# ============================================================================
# PREMIUM COLOR PALETTE - Sophisticated Navy/Gold scheme
# ============================================================================
class PremiumColors:
    # Primary colors
    NAVY_DARK = colors.HexColor('#0A1628')
    NAVY = colors.HexColor('#1B2838')
    NAVY_LIGHT = colors.HexColor('#2D4156')

    # Accent colors
    GOLD = colors.HexColor('#C9A227')
    GOLD_LIGHT = colors.HexColor('#E8D48B')
    TEAL = colors.HexColor('#0891B2')
    TEAL_LIGHT = colors.HexColor('#67E8F9')

    # Neutral colors
    WHITE = colors.HexColor('#FFFFFF')
    GRAY_100 = colors.HexColor('#F8FAFC')
    GRAY_200 = colors.HexColor('#E2E8F0')
    GRAY_300 = colors.HexColor('#CBD5E1')
    GRAY_500 = colors.HexColor('#64748B')
    GRAY_700 = colors.HexColor('#334155')
    GRAY_900 = colors.HexColor('#0F172A')

    # Chart colors
    CHART_1 = colors.HexColor('#0891B2')  # Teal
    CHART_2 = colors.HexColor('#C9A227')  # Gold
    CHART_3 = colors.HexColor('#059669')  # Emerald
    CHART_4 = colors.HexColor('#7C3AED')  # Purple
    CHART_5 = colors.HexColor('#DC2626')  # Red

# ============================================================================
# CUSTOM FLOWABLES
# ============================================================================

class GradientRect(Flowable):
    """Creates a gradient-filled rectangle"""
    def __init__(self, width, height, color1, color2, direction='horizontal'):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color1 = color1
        self.color2 = color2
        self.direction = direction

    def draw(self):
        # Simulate gradient with multiple rectangles
        steps = 50
        for i in range(steps):
            ratio = i / steps
            r = self.color1.red + (self.color2.red - self.color1.red) * ratio
            g = self.color1.green + (self.color2.green - self.color1.green) * ratio
            b = self.color1.blue + (self.color2.blue - self.color1.blue) * ratio
            self.canv.setFillColorRGB(r, g, b)
            if self.direction == 'horizontal':
                x = i * self.width / steps
                self.canv.rect(x, 0, self.width/steps + 1, self.height, fill=1, stroke=0)
            else:
                y = i * self.height / steps
                self.canv.rect(0, y, self.width, self.height/steps + 1, fill=1, stroke=0)

class KeyMetricBox(Flowable):
    """Creates a premium key metric callout box"""
    def __init__(self, value, label, width=120, height=80, accent_color=None):
        Flowable.__init__(self)
        self.value = value
        self.label = label
        self.box_width = width
        self.box_height = height
        self.accent_color = accent_color or PremiumColors.GOLD

    def wrap(self, availWidth, availHeight):
        return (self.box_width, self.box_height)

    def draw(self):
        # Background
        self.canv.setFillColor(PremiumColors.GRAY_100)
        self.canv.roundRect(0, 0, self.box_width, self.box_height, 8, fill=1, stroke=0)

        # Accent bar at top
        self.canv.setFillColor(self.accent_color)
        self.canv.rect(0, self.box_height - 4, self.box_width, 4, fill=1, stroke=0)

        # Value
        self.canv.setFillColor(PremiumColors.NAVY_DARK)
        self.canv.setFont("Helvetica-Bold", 20)
        self.canv.drawCentredString(self.box_width/2, self.box_height - 35, self.value)

        # Label
        self.canv.setFillColor(PremiumColors.GRAY_500)
        self.canv.setFont("Helvetica", 9)
        # Word wrap label
        words = self.label.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if self.canv.stringWidth(test_line, "Helvetica", 9) < self.box_width - 16:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        y_pos = self.box_height - 55
        for line in lines[:2]:  # Max 2 lines
            self.canv.drawCentredString(self.box_width/2, y_pos, line)
            y_pos -= 12

class SectionDivider(Flowable):
    """Creates a premium section divider"""
    def __init__(self, width, text=""):
        Flowable.__init__(self)
        self.div_width = width
        self.text = text

    def wrap(self, availWidth, availHeight):
        return (self.div_width, 30)

    def draw(self):
        # Draw line
        self.canv.setStrokeColor(PremiumColors.GOLD)
        self.canv.setLineWidth(2)
        self.canv.line(0, 15, self.div_width, 15)

        # Draw decorative elements
        self.canv.setFillColor(PremiumColors.GOLD)
        self.canv.circle(0, 15, 4, fill=1, stroke=0)
        self.canv.circle(self.div_width, 15, 4, fill=1, stroke=0)

class ChapterHeader(Flowable):
    """Creates a premium chapter header with number"""
    def __init__(self, number, title, width):
        Flowable.__init__(self)
        self.number = number
        self.title = title
        self.header_width = width

    def wrap(self, availWidth, availHeight):
        return (self.header_width, 60)

    def draw(self):
        # Chapter number box
        self.canv.setFillColor(PremiumColors.NAVY)
        self.canv.roundRect(0, 20, 40, 40, 4, fill=1, stroke=0)

        # Chapter number
        self.canv.setFillColor(PremiumColors.GOLD)
        self.canv.setFont("Helvetica-Bold", 20)
        self.canv.drawCentredString(20, 32, str(self.number))

        # Chapter title
        self.canv.setFillColor(PremiumColors.NAVY_DARK)
        self.canv.setFont("Helvetica-Bold", 22)
        self.canv.drawString(55, 32, self.title)

        # Underline
        self.canv.setStrokeColor(PremiumColors.GOLD)
        self.canv.setLineWidth(3)
        self.canv.line(55, 18, 55 + self.canv.stringWidth(self.title, "Helvetica-Bold", 22), 18)

# ============================================================================
# PAGE TEMPLATES
# ============================================================================

def create_cover_page(canvas, doc):
    """Creates the premium cover page"""
    canvas.saveState()
    width, height = A4

    # Full page navy background
    canvas.setFillColor(PremiumColors.NAVY_DARK)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)

    # Geometric accent pattern (top right)
    canvas.setFillColor(PremiumColors.NAVY)
    canvas.rect(width - 200, height - 300, 200, 300, fill=1, stroke=0)

    # Gold accent lines
    canvas.setStrokeColor(PremiumColors.GOLD)
    canvas.setLineWidth(3)
    canvas.line(50, height - 120, width - 50, height - 120)
    canvas.line(50, 120, width - 50, 120)

    # Gold accent rectangle
    canvas.setFillColor(PremiumColors.GOLD)
    canvas.rect(50, height - 140, 80, 4, fill=1, stroke=0)

    # Report type label
    canvas.setFillColor(PremiumColors.GOLD)
    canvas.setFont("Helvetica", 12)
    canvas.drawString(50, height - 100, "STRATEGIC MARKET INTELLIGENCE REPORT")

    # Main title
    canvas.setFillColor(PremiumColors.WHITE)
    canvas.setFont("Helvetica-Bold", 36)
    canvas.drawString(50, height - 200, "Global Antenna")
    canvas.drawString(50, height - 245, "Market Strategy")

    # Year badge
    canvas.setFillColor(PremiumColors.GOLD)
    canvas.setFont("Helvetica-Bold", 72)
    canvas.drawString(50, height - 340, "2026")

    # Subtitle
    canvas.setFillColor(PremiumColors.GRAY_300)
    canvas.setFont("Helvetica", 16)
    canvas.drawString(50, height - 400, "IoT and Robotics/Autonomous Systems Focus")

    # Target audience
    canvas.setFillColor(PremiumColors.TEAL_LIGHT)
    canvas.setFont("Helvetica-Oblique", 13)
    canvas.drawString(50, height - 430, "For German IoT Components Distributor & Systems Integrator")

    # Bottom section - Key highlights
    canvas.setFillColor(PremiumColors.GRAY_200)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(50, 200, "KEY MARKET HIGHLIGHTS")

    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(PremiumColors.GRAY_300)
    highlights = [
        "$15B+ IoT Antenna Market by 2026",
        "20% CAGR Growth Through 2030",
        "Germany: $2.34B Robotics Market by 2032",
        "5G & mmWave Technology Acceleration"
    ]
    y_pos = 175
    for h in highlights:
        canvas.setFillColor(PremiumColors.GOLD)
        canvas.circle(55, y_pos + 3, 3, fill=1, stroke=0)
        canvas.setFillColor(PremiumColors.GRAY_300)
        canvas.drawString(70, y_pos, h)
        y_pos -= 18

    # Footer
    canvas.setFillColor(PremiumColors.GRAY_500)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(50, 50, "December 2025  |  Strategic Planning Document  |  Classification: Confidential")

    # Company branding area
    canvas.setFillColor(PremiumColors.NAVY_LIGHT)
    canvas.roundRect(width - 200, 30, 150, 65, 5, fill=1, stroke=0)
    canvas.setFillColor(PremiumColors.GOLD)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawCentredString(width - 125, 72, "CRIMSON SUN")
    canvas.setFillColor(PremiumColors.WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawCentredString(width - 125, 58, "TECHNOLOGIES")
    canvas.setFillColor(PremiumColors.GRAY_300)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(width - 125, 42, "An Interstates & Vagabonds Company")

    canvas.restoreState()

def page_header_footer(canvas, doc):
    """Adds header and footer to content pages"""
    canvas.saveState()
    width, height = A4

    # Header bar
    canvas.setFillColor(PremiumColors.NAVY_DARK)
    canvas.rect(0, height - 40, width, 40, fill=1, stroke=0)

    # Header text
    canvas.setFillColor(PremiumColors.WHITE)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(50, height - 27, "Global Antenna Market Strategy Report 2026")

    # Gold accent
    canvas.setFillColor(PremiumColors.GOLD)
    canvas.rect(0, height - 43, width, 3, fill=1, stroke=0)

    # Footer
    canvas.setStrokeColor(PremiumColors.GRAY_200)
    canvas.setLineWidth(0.5)
    canvas.line(50, 45, width - 50, 45)

    canvas.setFillColor(PremiumColors.GRAY_500)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(50, 30, "Crimson Sun Technologies  |  IoT & Robotics/Autonomous Systems  |  German Market Focus")

    # Page number
    canvas.setFillColor(PremiumColors.NAVY)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawRightString(width - 50, 30, f"Page {doc.page}")

    # Confidential watermark (subtle)
    canvas.setFillColor(PremiumColors.GRAY_200)
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(width - 50, height - 27, "CONFIDENTIAL")

    canvas.restoreState()

# ============================================================================
# STYLES
# ============================================================================

def get_premium_styles():
    """Returns premium paragraph styles"""
    styles = getSampleStyleSheet()

    # Executive Summary Title
    styles.add(ParagraphStyle(
        name='ExecTitle',
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=PremiumColors.NAVY_DARK,
        spaceAfter=20,
        spaceBefore=30,
        leading=34
    ))

    # Section Header (H1)
    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=PremiumColors.NAVY_DARK,
        spaceAfter=15,
        spaceBefore=25,
        leading=28
    ))

    # Subsection Header (H2)
    styles.add(ParagraphStyle(
        name='SubsectionHeader',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=PremiumColors.NAVY,
        spaceAfter=10,
        spaceBefore=20,
        leading=20
    ))

    # Sub-subsection Header (H3)
    styles.add(ParagraphStyle(
        name='H3Header',
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=PremiumColors.NAVY_LIGHT,
        spaceAfter=8,
        spaceBefore=15,
        leading=16
    ))

    # Body text
    styles.add(ParagraphStyle(
        name='PremiumBody',
        fontName='Helvetica',
        fontSize=10,
        textColor=PremiumColors.GRAY_700,
        spaceAfter=10,
        spaceBefore=0,
        leading=15,
        alignment=TA_JUSTIFY
    ))

    # Bullet point text
    styles.add(ParagraphStyle(
        name='BulletText',
        fontName='Helvetica',
        fontSize=10,
        textColor=PremiumColors.GRAY_700,
        spaceAfter=5,
        spaceBefore=0,
        leading=14,
        leftIndent=20,
        bulletIndent=10
    ))

    # Key insight box
    styles.add(ParagraphStyle(
        name='InsightText',
        fontName='Helvetica-Oblique',
        fontSize=11,
        textColor=PremiumColors.NAVY,
        spaceAfter=5,
        spaceBefore=5,
        leading=15,
        leftIndent=15,
        rightIndent=15
    ))

    # Table header
    styles.add(ParagraphStyle(
        name='TableHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=PremiumColors.WHITE,
        alignment=TA_CENTER
    ))

    # Table cell
    styles.add(ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=9,
        textColor=PremiumColors.GRAY_700,
        alignment=TA_LEFT
    ))

    # TOC entry
    styles.add(ParagraphStyle(
        name='TOCEntry',
        fontName='Helvetica',
        fontSize=11,
        textColor=PremiumColors.GRAY_700,
        spaceAfter=8,
        leading=16
    ))

    # TOC Section
    styles.add(ParagraphStyle(
        name='TOCSection',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=PremiumColors.NAVY,
        spaceAfter=5,
        spaceBefore=15,
        leading=16
    ))

    # Caption
    styles.add(ParagraphStyle(
        name='Caption',
        fontName='Helvetica-Oblique',
        fontSize=9,
        textColor=PremiumColors.GRAY_500,
        spaceAfter=15,
        spaceBefore=5,
        alignment=TA_CENTER
    ))

    # Quote/Callout
    styles.add(ParagraphStyle(
        name='Callout',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=PremiumColors.NAVY,
        spaceAfter=10,
        spaceBefore=10,
        leading=20,
        leftIndent=30,
        rightIndent=30,
        alignment=TA_CENTER
    ))

    return styles

# ============================================================================
# CHART GENERATION
# ============================================================================

def create_market_growth_chart():
    """Creates IoT antenna market growth projection chart"""
    fig, ax = plt.subplots(figsize=(7, 4))

    years = ['2024', '2025', '2026', '2027', '2028', '2029', '2030']
    iot_values = [1.2, 1.44, 1.73, 2.08, 2.50, 3.00, 3.58]
    drone_values = [1.2, 1.35, 1.52, 1.71, 1.93, 2.17, 2.44]
    amr_values = [0.5, 0.58, 0.67, 0.77, 0.89, 1.02, 1.17]

    x = range(len(years))
    width = 0.25

    bars1 = ax.bar([i - width for i in x], iot_values, width, label='IoT Antennas', color='#0891B2')
    bars2 = ax.bar(x, drone_values, width, label='Drone/UAV Antennas', color='#C9A227')
    bars3 = ax.bar([i + width for i in x], amr_values, width, label='AMR Antennas', color='#059669')

    ax.set_xlabel('Year', fontsize=10, color='#334155')
    ax.set_ylabel('Market Size (USD Billion)', fontsize=10, color='#334155')
    ax.set_title('Antenna Market Growth Projections by Segment', fontsize=14, fontweight='bold', color='#1B2838', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.legend(loc='upper left', frameon=True, fancybox=True)
    ax.set_ylim(0, 4.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0.8:
                ax.annotate(f'${height:.2f}B',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=7, color='#334155')

    plt.tight_layout()

    # Save to buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close()

    return buf

def create_regional_market_chart():
    """Creates regional market distribution pie chart"""
    fig, ax = plt.subplots(figsize=(6, 4))

    regions = ['North America\n(35%)', 'Europe\n(30%)', 'Asia-Pacific\n(25%)', 'Emerging\nMarkets (10%)']
    sizes = [35, 30, 25, 10]
    colors_list = ['#0891B2', '#C9A227', '#059669', '#7C3AED']
    explode = (0.02, 0.02, 0.02, 0.02)

    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=regions, colors=colors_list,
                                       autopct='', startangle=90, pctdistance=0.75)

    # Style labels
    for text in texts:
        text.set_fontsize(9)
        text.set_color('#334155')

    ax.set_title('Global Antenna Market by Region (2025)', fontsize=14, fontweight='bold', color='#1B2838', pad=20)

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close()

    return buf

def create_germany_market_chart():
    """Creates Germany-specific market opportunity chart"""
    fig, ax = plt.subplots(figsize=(7, 4))

    categories = ['Warehouse\nRobotics', 'Industrial\nIoT', 'Autonomous\nSystems', 'Commercial\nDrones']
    values_2024 = [0.82, 0.65, 0.45, 0.25]
    values_2030 = [2.34, 1.85, 1.20, 0.75]

    x = range(len(categories))
    width = 0.35

    bars1 = ax.bar([i - width/2 for i in x], values_2024, width, label='2024', color='#CBD5E1')
    bars2 = ax.bar([i + width/2 for i in x], values_2030, width, label='2030/32 Projected', color='#C9A227')

    ax.set_ylabel('Market Size (USD Billion)', fontsize=10, color='#334155')
    ax.set_title('Germany: Key Market Segments Growth', fontsize=14, fontweight='bold', color='#1B2838', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend(loc='upper left', frameon=True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)

    # Add growth percentages
    for i, (v1, v2) in enumerate(zip(values_2024, values_2030)):
        growth = ((v2 - v1) / v1) * 100
        ax.annotate(f'+{growth:.0f}%',
                   xy=(i + width/2, v2),
                   xytext=(0, 5),
                   textcoords="offset points",
                   ha='center', va='bottom', fontsize=9, fontweight='bold', color='#059669')

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close()

    return buf

def create_cagr_comparison_chart():
    """Creates CAGR comparison horizontal bar chart"""
    fig, ax = plt.subplots(figsize=(7, 4))

    segments = ['IoT Antennas', 'mmWave/Phased Array', 'Germany Warehouse\nRobotics',
                'Autonomous Navigation', 'AMR Market', 'Drone/UAV Antennas']
    cagr_values = [20.0, 21.6, 16.4, 17.1, 15.1, 12.5]
    colors_list = ['#0891B2', '#C9A227', '#059669', '#7C3AED', '#DC2626', '#64748B']

    bars = ax.barh(segments, cagr_values, color=colors_list, height=0.6)

    ax.set_xlabel('CAGR (%)', fontsize=10, color='#334155')
    ax.set_title('Growth Rates Comparison: Key Market Segments', fontsize=14, fontweight='bold', color='#1B2838', pad=20)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', alpha=0.3)
    ax.set_xlim(0, 25)

    # Add value labels
    for bar, val in zip(bars, cagr_values):
        ax.text(val + 0.5, bar.get_y() + bar.get_height()/2, f'{val}%',
               va='center', fontsize=10, fontweight='bold', color='#334155')

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close()

    return buf

def create_timeline_chart():
    """Creates implementation timeline visualization"""
    fig, ax = plt.subplots(figsize=(8, 3))

    # Timeline data
    quarters = ['Q1 2026', 'Q2 2026', 'Q3 2026', 'Q4 2026']
    phases = ['Foundation', 'Launch', 'Scale', 'Optimize']
    colors_list = ['#0891B2', '#C9A227', '#059669', '#7C3AED']

    for i, (q, p, c) in enumerate(zip(quarters, phases, colors_list)):
        # Draw rectangle for each phase
        rect = mpatches.FancyBboxPatch((i*2, 0.3), 1.8, 0.4,
                                        boxstyle="round,pad=0.02,rounding_size=0.1",
                                        facecolor=c, edgecolor='none', alpha=0.9)
        ax.add_patch(rect)

        # Quarter label
        ax.text(i*2 + 0.9, 0.1, q, ha='center', va='center', fontsize=10, fontweight='bold', color='#334155')

        # Phase label
        ax.text(i*2 + 0.9, 0.5, p, ha='center', va='center', fontsize=11, fontweight='bold', color='white')

        # Connecting arrow (except last)
        if i < 3:
            ax.annotate('', xy=(i*2 + 2, 0.5), xytext=(i*2 + 1.85, 0.5),
                       arrowprops=dict(arrowstyle='->', color='#64748B', lw=2))

    ax.set_xlim(-0.2, 8)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_title('2026 Implementation Roadmap', fontsize=14, fontweight='bold', color='#1B2838', pad=20)

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close()

    return buf

def create_portfolio_allocation_chart():
    """Creates product portfolio allocation chart"""
    fig, ax = plt.subplots(figsize=(5, 5))

    tiers = ['Tier A: Core\nHigh-Volume\n(70%)', 'Tier B: Differentiated\nSolutions\n(20%)',
             'Tier C: Emerging/\nSpecialized\n(10%)']
    sizes = [70, 20, 10]
    colors_list = ['#0891B2', '#C9A227', '#059669']

    wedges, texts = ax.pie(sizes, labels=tiers, colors=colors_list,
                           startangle=90, wedgeprops=dict(width=0.5))

    for text in texts:
        text.set_fontsize(9)
        text.set_color('#334155')

    # Add center text
    ax.text(0, 0, 'Portfolio\nStrategy', ha='center', va='center', fontsize=12, fontweight='bold', color='#1B2838')

    ax.set_title('Recommended Product Portfolio Allocation', fontsize=14, fontweight='bold', color='#1B2838', pad=20)

    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close()

    return buf

# ============================================================================
# CONTENT BUILDERS
# ============================================================================

def build_toc(styles):
    """Builds table of contents"""
    story = []

    story.append(Paragraph("Table of Contents", styles['ExecTitle']))
    story.append(Spacer(1, 20))

    toc_items = [
        ("1", "Executive Summary", "3"),
        ("2", "Market Overview and Sizing", "4"),
        ("", "Total Addressable Market", "4"),
        ("", "Market Drivers and Growth Catalysts", "5"),
        ("3", "Technology Trends and Product Evolution", "7"),
        ("", "Antenna Type Segmentation", "7"),
        ("", "Frequency Band Prioritization", "8"),
        ("", "Key Technology Innovations", "9"),
        ("4", "Competitive Landscape Analysis", "10"),
        ("", "Global Manufacturers Ecosystem", "10"),
        ("", "Market Share Dynamics", "12"),
        ("5", "Regional Insights: Germany-Specific Opportunities", "13"),
        ("", "German Industrial Robotics and IoT Market", "13"),
        ("", "Regulatory Environment", "14"),
        ("6", "Strategic Recommendations for 2026", "15"),
        ("", "Product Portfolio Architecture", "15"),
        ("", "Market Segmentation and Vertical Focus", "16"),
        ("", "Distribution and Channel Strategy", "17"),
        ("", "Technical Capability Development", "18"),
        ("", "Partnerships and Strategic Alliances", "19"),
        ("", "Pricing and Margin Strategy", "20"),
        ("", "Marketing and Brand Positioning", "21"),
        ("7", "Risk Analysis and Mitigation", "22"),
        ("8", "Implementation Timeline", "23"),
        ("9", "Success Metrics and KPIs", "24"),
        ("10", "Conclusion", "25"),
        ("", "References", "26"),
    ]

    for num, title, page in toc_items:
        if num:
            style = styles['TOCSection']
            prefix = f"<b>{num}.</b> "
        else:
            style = styles['TOCEntry']
            prefix = "     "

        # Create dotted leader line effect
        text = f"{prefix}{title} {'.' * 50} {page}"
        story.append(Paragraph(text[:80], style))

    story.append(PageBreak())
    return story

def build_executive_summary(styles):
    """Builds the executive summary section"""
    story = []

    story.append(ChapterHeader(1, "Executive Summary", 450))
    story.append(Spacer(1, 20))

    # Key metrics row
    metrics_data = [
        [
            KeyMetricBox("$15B+", "IoT Antenna Market 2026", accent_color=PremiumColors.TEAL),
            KeyMetricBox("20%", "CAGR Through 2030", accent_color=PremiumColors.GOLD),
            KeyMetricBox("$3.5B", "Drone Antenna Market 2033", accent_color=PremiumColors.CHART_3),
            KeyMetricBox("16.4%", "German Robotics CAGR", accent_color=PremiumColors.CHART_4)
        ]
    ]

    metrics_table = Table(metrics_data, colWidths=[125, 125, 125, 125])
    metrics_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 25))

    # Executive summary text
    exec_text = """The global antenna market for Internet of Things (IoT) and autonomous systems is
    experiencing unprecedented growth, presenting significant strategic opportunities for German
    components distributors and systems integrators entering 2026. The IoT antenna segment alone
    is projected to exceed USD 15 billion by 2026, growing at a compound annual growth rate (CAGR)
    of over 20% through 2030."""
    story.append(Paragraph(exec_text, styles['PremiumBody']))

    exec_text2 = """When combined with the robotics, autonomous mobile robots (AMR), and drone
    communication segments, the addressable market spans multiple high-growth verticals with
    distinct technology requirements and regional opportunities. This report provides a comprehensive
    analysis specifically tailored for a German distributor seeking to maximize market share in 2026."""
    story.append(Paragraph(exec_text2, styles['PremiumBody']))
    story.append(Spacer(1, 15))

    # Key findings callout box
    story.append(Paragraph("<b>KEY FINDINGS</b>", styles['SubsectionHeader']))

    findings = [
        "Global IoT antenna market projected at <b>$1.73 billion in 2026</b>, accelerating to $3.58 billion by 2030",
        "Drone/UAV antenna market growing at <b>12.5% CAGR</b>, reaching $3.5 billion by 2033",
        "Autonomous mobile robot communication segment expanding at <b>15% CAGR</b>, driven by warehouse automation",
        "Germany-specific industrial robotics market: <b>$0.82B (2024) → $2.34B (2032)</b> at 16.4% CAGR",
        "5G and sub-6 GHz spectrum adoption accelerating IoT device proliferation",
        "Phased array antennas (MIMO, beamforming) becoming essential for high-bandwidth autonomous applications",
        "Regulatory environment increasingly favorable for autonomous systems with standardized EU framework"
    ]

    for finding in findings:
        bullet_para = Paragraph(f"• {finding}", styles['BulletText'])
        story.append(bullet_para)

    story.append(PageBreak())
    return story

def build_market_overview(styles):
    """Builds the market overview section"""
    story = []

    story.append(ChapterHeader(2, "Market Overview and Sizing", 450))
    story.append(Spacer(1, 20))

    # TAM section
    story.append(Paragraph("Total Addressable Market (TAM)", styles['SubsectionHeader']))

    tam_text = """The antenna market encompasses diverse applications and frequency bands. The broader
    antenna market (all segments) is valued at USD 25.31 billion in 2025 and projected to reach
    USD 36.93 billion by 2030 at a CAGR of 7.85%. Within this landscape, three primary segments
    are highly relevant for your organization."""
    story.append(Paragraph(tam_text, styles['PremiumBody']))
    story.append(Spacer(1, 15))

    # Market segments table
    story.append(Paragraph("Primary Market Segments", styles['H3Header']))

    segments_data = [
        [Paragraph('<b>Segment</b>', styles['TableHeader']),
         Paragraph('<b>2024 Size</b>', styles['TableHeader']),
         Paragraph('<b>2026 Projected</b>', styles['TableHeader']),
         Paragraph('<b>2030+ Target</b>', styles['TableHeader']),
         Paragraph('<b>CAGR</b>', styles['TableHeader'])],
        ['IoT Antennas', '$1.2B', '$1.73B', '$3.58B (2030)', '20%'],
        ['Drone/UAV Antennas', '$1.2B', '$1.52B', '$3.5B (2033)', '12.5%'],
        ['AMR Systems', '$0.5B', '$0.67B', '$1.17B (2030)', '15%'],
    ]

    segments_table = Table(segments_data, colWidths=[120, 80, 90, 100, 60])
    segments_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PremiumColors.NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), PremiumColors.WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), PremiumColors.GRAY_100),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [PremiumColors.WHITE, PremiumColors.GRAY_100]),
        ('GRID', (0, 0), (-1, -1), 0.5, PremiumColors.GRAY_200),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
    ]))
    story.append(segments_table)
    story.append(Paragraph("Source: Multiple industry analysts (see References)", styles['Caption']))

    # Combined market opportunity callout
    callout_text = """\"The combined addressable market for IoT, robotics, and autonomous systems antennas
    is estimated at approximately <b>USD 5.5 billion globally in 2024</b>, projected to grow to
    <b>USD 8+ billion by 2028</b>, representing a compound opportunity of USD 18-20 billion over
    the next four years.\""""
    story.append(Spacer(1, 10))
    story.append(Paragraph(callout_text, styles['Callout']))
    story.append(Spacer(1, 20))

    # Market drivers section
    story.append(Paragraph("Market Drivers and Growth Catalysts", styles['SubsectionHeader']))

    # Driver 1
    story.append(Paragraph("<b>1. Industry 4.0 and Digital Transformation</b>", styles['H3Header']))
    driver1_text = """Germany's industrial sector is undergoing systematic digital transformation driven
    by the Industry 4.0 initiative. This creates substantial demand for connected sensors and IoT devices
    on production lines, real-time communication systems for automated warehouses, and high-reliability,
    low-latency connectivity for autonomous robots."""
    story.append(Paragraph(driver1_text, styles['PremiumBody']))

    # Driver 2
    story.append(Paragraph("<b>2. 5G Deployment and Spectrum Harmonization</b>", styles['H3Header']))
    driver2_text = """European 5G rollout is accelerating with harmonized spectrum bands now standardized.
    The 3.4-3.8 GHz band provides primary 5G coverage with 400 MHz harmonized across EU, while the
    26 GHz band enables high-capacity mmWave for industrial applications."""
    story.append(Paragraph(driver2_text, styles['PremiumBody']))

    # Spectrum bands table
    spectrum_data = [
        [Paragraph('<b>Band</b>', styles['TableHeader']),
         Paragraph('<b>Frequency</b>', styles['TableHeader']),
         Paragraph('<b>Application</b>', styles['TableHeader'])],
        ['Primary 5G', '3.4-3.8 GHz', 'Industrial IoT, main coverage'],
        ['mmWave', '26 GHz', 'High-capacity industrial automation'],
        ['Sub-6 GHz', '700 MHz, 2.6 GHz', 'Nationwide IoT coverage'],
    ]

    spectrum_table = Table(spectrum_data, colWidths=[100, 120, 230])
    spectrum_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PremiumColors.TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), PremiumColors.WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [PremiumColors.WHITE, PremiumColors.GRAY_100]),
        ('GRID', (0, 0), (-1, -1), 0.5, PremiumColors.GRAY_200),
    ]))
    story.append(spectrum_table)
    story.append(Spacer(1, 15))

    # Driver 3
    story.append(Paragraph("<b>3. Autonomous Systems Market Expansion</b>", styles['H3Header']))
    driver3_text = """Multiple autonomous system categories are driving antenna demand. The drone market
    is projected at USD 45.8 billion by 2025 growing at 20.5% CAGR, with commercial applications
    (42.7% of market) increasingly dominating over military. The global AMR market is expected to
    grow from $2.01 billion (2024) to $4.56 billion (2030) at 15.1% CAGR."""
    story.append(Paragraph(driver3_text, styles['PremiumBody']))

    # Driver 4
    story.append(Paragraph("<b>4. AI-Driven Optimization and Adaptive Antenna Systems</b>", styles['H3Header']))
    driver4_text = """Emerging trends in phased array and MIMO antenna technology include AI-enabled
    beamforming for optimized signal transmission, adaptive antenna tuning reducing energy consumption,
    and predictive antenna performance optimization for autonomous systems. This creates differentiation
    opportunities for distributors offering "intelligent antenna solutions" with embedded optimization capabilities."""
    story.append(Paragraph(driver4_text, styles['PremiumBody']))

    # Driver 5
    story.append(Paragraph("<b>5. Labor Shortages and Automation Imperative</b>", styles['H3Header']))
    driver5_text = """Germany faces structural labor shortage challenges including aging workforce
    demographics, persistent skilled labor shortages across logistics and production, and rising
    labor costs driving ROI optimization on automation. Companies investing in robotics require
    reliable wireless infrastructure to maximize ROI on these capital-intensive investments."""
    story.append(Paragraph(driver5_text, styles['PremiumBody']))

    story.append(PageBreak())
    return story

def build_technology_trends(styles):
    """Builds the technology trends section"""
    story = []

    story.append(ChapterHeader(3, "Technology Trends and Product Evolution", 450))
    story.append(Spacer(1, 20))

    intro_text = """The antenna market is evolving toward integrated, multi-functional solutions
    supporting diverse frequency bands and performance requirements. Understanding these technology
    trends is critical for portfolio decisions and competitive positioning."""
    story.append(Paragraph(intro_text, styles['PremiumBody']))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Antenna Type Segmentation", styles['SubsectionHeader']))

    # Antenna types
    antenna_types = [
        ("1. PCB Antennas (Antenna-on-Board)",
         "Compact, cost-effective, integrated into device PCBs. Best for mass-market IoT devices, wearables, low-power sensors. Entry-level segment with high volume but lower margins."),
        ("2. Chip Antennas and LDS (Laser Direct Structuring)",
         "Miniaturized, flexible 3D designs with multiple band support. 15-20% CAGR growth as form-factor constraints increase. High-value market with stronger margins for specialized applications."),
        ("3. Phased Array Antennas and MIMO Systems",
         "Electronic beam steering, beamforming, multiple simultaneous beams. Critical for 5G infrastructure, autonomous vehicles, and high-performance robotics. mmWave segment growing at 21.6% CAGR."),
        ("4. Integrated Antenna Modules (AiP)",
         "Complete antenna system with RF front-end integrated into single package. Fastest-growing antenna technology segment. Requires deep integration partnerships and technical expertise."),
        ("5. SATCOM Antennas",
         "Multi-band (L, Ku, C, X), high-performance directional solutions. Niche but high-value for extended-range autonomous systems combining terrestrial and satellite connectivity."),
    ]

    for title, desc in antenna_types:
        story.append(Paragraph(f"<b>{title}</b>", styles['H3Header']))
        story.append(Paragraph(desc, styles['PremiumBody']))

    story.append(Spacer(1, 15))
    story.append(Paragraph("Key Technology Innovations Reshaping the Market", styles['SubsectionHeader']))

    innovations = [
        ("<b>Beamforming and Adaptive Antenna Control:</b> Electronic beam steering eliminating mechanical repositioning. AI-driven beam optimization reducing power consumption 15-30%."),
        ("<b>MIMO and Spatial Multiplexing:</b> Multiple antenna elements enabling parallel data streams. Performance scaling with antenna element count (8x, 16x, 32x arrays increasingly common)."),
        ("<b>Antenna-in-Package Integration:</b> Reduces system size, power consumption, and manufacturing complexity. Enables faster device design cycles."),
        ("<b>Multi-Band Integration:</b> Single antenna supporting 4-8 frequency bands simultaneously. Cost reduction and future-proofing as spectrum allocations evolve."),
        ("<b>Energy Efficiency Optimization:</b> Low-power antenna designs extending battery life. Power-efficient beamforming reducing transmit power requirements 20-40%.")
    ]

    for innovation in innovations:
        story.append(Paragraph(f"• {innovation}", styles['BulletText']))

    story.append(PageBreak())
    return story

def build_competitive_landscape(styles):
    """Builds the competitive landscape section"""
    story = []

    story.append(ChapterHeader(4, "Competitive Landscape Analysis", 450))
    story.append(Spacer(1, 20))

    intro_text = """The antenna manufacturing industry is characterized by large infrastructure companies
    dominating telecom basestation segments, specialized manufacturers serving IoT and vertical applications,
    and emerging pure-play antenna technology companies focusing on advanced solutions."""
    story.append(Paragraph(intro_text, styles['PremiumBody']))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Tier 1 Global Players", styles['SubsectionHeader']))

    # Competitors table
    competitors_data = [
        [Paragraph('<b>Company</b>', styles['TableHeader']),
         Paragraph('<b>HQ</b>', styles['TableHeader']),
         Paragraph('<b>Specialization</b>', styles['TableHeader']),
         Paragraph('<b>Market Position</b>', styles['TableHeader']),
         Paragraph('<b>Strategic Relevance</b>', styles['TableHeader'])],
        ['Huawei', 'China', 'Telecom infrastructure, 5G, IoT modules', 'Market leader (~15% share)', 'Cost competition'],
        ['Ericsson', 'Sweden', '5G macro antennas, beamforming', 'Tier 1 infrastructure', 'Partnership opportunity'],
        ['CommScope', 'USA', 'Wireless infrastructure, passive/active', 'Market incumbent', 'Established distribution'],
        ['Amphenol', 'USA', 'Diverse portfolio (PCB, chip, LDS)', 'Growing IoT specialist', 'Compatible partner model'],
        ['Taoglas', 'Ireland', 'IoT antennas, 5G/LTE, automotive', 'Focused IoT player', 'Technical expertise'],
        ['Kathrein', 'Germany', 'Telecom, 5G, automotive', 'European heritage', 'Competitor + potential partner'],
        ['Murata', 'Japan', 'Integrated modules, chip antennas, AiP', 'Miniaturization leader', 'Premium positioning'],
    ]

    comp_table = Table(competitors_data, colWidths=[70, 50, 130, 100, 100])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PremiumColors.NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), PremiumColors.WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [PremiumColors.WHITE, PremiumColors.GRAY_100]),
        ('GRID', (0, 0), (-1, -1), 0.5, PremiumColors.GRAY_200),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 15))

    # Market share section
    story.append(Paragraph("Market Share Dynamics (2025)", styles['SubsectionHeader']))

    share_text = """The antenna market is fragmented, with no single company holding >20% global share.
    Regional variations are significant, with North America representing 35% of total market value,
    Europe at 30%, Asia-Pacific at 25%, and emerging markets at 10%."""
    story.append(Paragraph(share_text, styles['PremiumBody']))
    story.append(Spacer(1, 10))

    # Competitive advantages
    story.append(Paragraph("Competitive Advantages for German Distributors", styles['SubsectionHeader']))

    advantages = [
        "<b>Engineering & Systems Integration Expertise:</b> Differentiate through application-specific antenna design consulting and integration services",
        "<b>Quality and Reliability Standards:</b> German engineering reputation supports premium positioning in European markets",
        "<b>Local Presence:</b> Proximity to major manufacturing clusters (Bavaria, Baden-Württemberg) enables faster support and customization",
        "<b>Industry 4.0 Alignment:</b> Deep understanding of Industry 4.0 requirements positions distributor as trusted advisor",
        "<b>Regulatory Expertise:</b> Familiarity with European spectrum requirements provides advantage over non-European competitors",
        "<b>Sustainability/ESG:</b> German stakeholders increasingly demand environmental compliance and lifecycle sustainability"
    ]

    for adv in advantages:
        story.append(Paragraph(f"• {adv}", styles['BulletText']))

    story.append(PageBreak())
    return story

def build_regional_insights(styles):
    """Builds the Germany-specific regional insights section"""
    story = []

    story.append(ChapterHeader(5, "Regional Insights: Germany", 450))
    story.append(Spacer(1, 20))

    story.append(Paragraph("German Industrial Robotics and IoT Market Context", styles['SubsectionHeader']))

    context_text = """Germany's manufacturing sector is at the epicenter of global robotics and automation
    adoption. The German warehouse robotics market is projected to grow from USD 0.82 billion (2024)
    to USD 2.34 billion (2032) at 16.4% CAGR. The global robotics technology market is projected at
    €150.7 billion by 2028 at 13% CAGR, with Germany as a key hub."""
    story.append(Paragraph(context_text, styles['PremiumBody']))
    story.append(Spacer(1, 15))

    # Geographic concentration
    story.append(Paragraph("Geographic Concentration", styles['H3Header']))

    geo_data = [
        [Paragraph('<b>Region</b>', styles['TableHeader']),
         Paragraph('<b>Market Share</b>', styles['TableHeader']),
         Paragraph('<b>Key Industries & Players</b>', styles['TableHeader'])],
        ['Bavaria', '30%', 'Munich, Nuremberg tech corridors; BMW, Audi, Siemens, Infineon'],
        ['Baden-Württemberg', '25%', 'Stuttgart automotive cluster; Mercedes-Benz, Porsche, Bosch, Festo'],
        ['North Rhine-Westphalia', '20%', 'Industrial manufacturing; chemical industry concentration'],
        ['Lower Saxony', '15%', 'Volkswagen Wolfsburg; agricultural processing'],
        ['Eastern Germany', '10%', 'Emerging manufacturing centers in Saxony, Thuringia'],
    ]

    geo_table = Table(geo_data, colWidths=[130, 80, 240])
    geo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PremiumColors.GOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), PremiumColors.NAVY_DARK),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [PremiumColors.WHITE, PremiumColors.GRAY_100]),
        ('GRID', (0, 0), (-1, -1), 0.5, PremiumColors.GRAY_200),
    ]))
    story.append(geo_table)
    story.append(Spacer(1, 20))

    # Regulatory environment
    story.append(Paragraph("Regulatory Environment", styles['SubsectionHeader']))

    story.append(Paragraph("<b>5G Spectrum Allocation (Germany)</b>", styles['H3Header']))
    reg_text = """Germany implements EU-harmonized regulations with additional national requirements.
    The 3.4-3.8 GHz band (300 MHz auctioned to major carriers) is the primary 5G deployment band.
    The 26 GHz band is reserved for high-capacity, local, and vertical applications with increasing
    allocation to private industrial networks."""
    story.append(Paragraph(reg_text, styles['PremiumBody']))

    story.append(Paragraph("<b>Strategic Implications:</b>", styles['H3Header']))
    implications = [
        "Antenna portfolio should prioritize 3.4-3.8 GHz and 26 GHz solutions",
        "Private network antenna systems are emerging vertical opportunity in industrial zones",
        "Sub-6 GHz antennas remain essential for broad IoT device coverage"
    ]
    for imp in implications:
        story.append(Paragraph(f"• {imp}", styles['BulletText']))

    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Drone and Autonomous Systems Regulation</b>", styles['H3Header']))
    drone_text = """German law implements EASA standards with national enhancements. Drones under 25kg
    are classified as "open category" requiring operator identification/registration. Autonomous drone
    operations (beyond visual line of sight) are restricted to specific authorized corridors.
    This regulatory complexity creates consulting and integration opportunities."""
    story.append(Paragraph(drone_text, styles['PremiumBody']))

    story.append(PageBreak())
    return story

def build_strategic_recommendations(styles):
    """Builds the strategic recommendations section"""
    story = []

    story.append(ChapterHeader(6, "Strategic Recommendations for 2026", 450))
    story.append(Spacer(1, 20))

    # 1. Product Portfolio
    story.append(Paragraph("1. Product Portfolio Architecture", styles['SubsectionHeader']))

    portfolio_text = """A tiered portfolio approach balances volume, margin, and strategic positioning:"""
    story.append(Paragraph(portfolio_text, styles['PremiumBody']))

    portfolio_data = [
        [Paragraph('<b>Tier</b>', styles['TableHeader']),
         Paragraph('<b>Focus (%)</b>', styles['TableHeader']),
         Paragraph('<b>Products</b>', styles['TableHeader']),
         Paragraph('<b>Margin Target</b>', styles['TableHeader'])],
        ['Tier A: Core High-Volume', '70%', 'Sub-6 GHz antennas (700 MHz, 2.6 GHz, 3.4-3.8 GHz)', '20-35%'],
        ['Tier B: Differentiated', '20%', '26 GHz mmWave, Phased array/MIMO, AiP modules', '35-50%'],
        ['Tier C: Emerging/Specialized', '10%', 'SATCOM integrated, AI-optimized, multi-band agile', '40-60%'],
    ]

    portfolio_table = Table(portfolio_data, colWidths=[120, 60, 200, 70])
    portfolio_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PremiumColors.NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), PremiumColors.WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [PremiumColors.WHITE, PremiumColors.GRAY_100]),
        ('GRID', (0, 0), (-1, -1), 0.5, PremiumColors.GRAY_200),
    ]))
    story.append(portfolio_table)
    story.append(Spacer(1, 20))

    # 2. Vertical Focus
    story.append(Paragraph("2. Market Segmentation and Vertical Focus", styles['SubsectionHeader']))

    verticals = [
        ("Vertical 1: Warehouse Automation & E-Commerce Logistics", "HIGHEST PRIORITY",
         "AMR market growing 18.8% CAGR. Target 3PL providers, e-commerce fulfillment, warehouse automation companies. Margin profile: 30-45%."),
        ("Vertical 2: Autonomous Vehicles and Robotics", "HIGH PRIORITY",
         "Autonomous navigation market $3.27B → $15.91B at 17.1% CAGR. Target automotive suppliers, robotics OEMs. Margin profile: 25-40%."),
        ("Vertical 3: Industrial IoT and Smart Manufacturing", "HIGH PRIORITY",
         "German Industry 4.0 adoption driving private network deployments. Target precision manufacturing, automotive suppliers. Margin profile: 40-55%."),
        ("Vertical 4: Commercial Drones", "MEDIUM PRIORITY",
         "Drone market $45.8B growing at 20.5% CAGR. Target drone manufacturers, commercial operators. Margin profile: 35-50%."),
    ]

    for title, priority, desc in verticals:
        story.append(Paragraph(f"<b>{title}</b> <font color='#C9A227'>[{priority}]</font>", styles['H3Header']))
        story.append(Paragraph(desc, styles['PremiumBody']))

    story.append(Spacer(1, 15))

    # 3. Distribution Strategy
    story.append(Paragraph("3. Distribution and Channel Strategy", styles['SubsectionHeader']))

    channel_data = [
        [Paragraph('<b>Channel</b>', styles['TableHeader']),
         Paragraph('<b>Revenue Target</b>', styles['TableHeader']),
         Paragraph('<b>Focus</b>', styles['TableHeader'])],
        ['Direct Sales', '40%', 'Tier 1/2 customers, OEMs, major system integrators'],
        ['Engineering Partners', '25%', 'Systems integrators specializing in automation, IIoT'],
        ['Reseller Networks', '20%', 'Industrial electronics distributors'],
        ['OEM Partnerships', '15%', 'Exclusive/preferred supplier arrangements with drone/robotics OEMs'],
    ]

    channel_table = Table(channel_data, colWidths=[120, 90, 240])
    channel_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PremiumColors.TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), PremiumColors.WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [PremiumColors.WHITE, PremiumColors.GRAY_100]),
        ('GRID', (0, 0), (-1, -1), 0.5, PremiumColors.GRAY_200),
    ]))
    story.append(channel_table)
    story.append(Spacer(1, 15))

    # 4. Technical Capability
    story.append(Paragraph("4. Technical Capability Development", styles['SubsectionHeader']))

    capabilities = [
        ("<b>Antenna Measurement and Testing Lab</b> (€150-300K investment): Network analyzer, anechoic chamber partnership. Enables premium pricing for validated solutions."),
        ("<b>RF Design and Integration Consulting</b> (€250-400K annually): 2-3 RF engineers with antenna design background. Enables 40-55% margin on engineering services."),
        ("<b>5G Private Network Architecture Expertise</b> (€80-150K training): Advanced training in private 5G network design. High-margin vertical in German industrial market."),
        ("<b>Drone Connectivity Consulting</b> (€100-200K development): Extended-range antenna solutions, telemetry optimization. 35-50% margins on system offerings.")
    ]

    for cap in capabilities:
        story.append(Paragraph(f"• {cap}", styles['BulletText']))

    story.append(PageBreak())

    # 5. Partnerships
    story.append(Paragraph("5. Partnerships and Strategic Alliances", styles['SubsectionHeader']))

    story.append(Paragraph("<b>Tier 1 Supplier Relationships:</b>", styles['H3Header']))
    suppliers = [
        "Amphenol (primary multi-line supplier): Negotiate exclusive distributor status for German regions/verticals",
        "Taoglas (IoT specialist): Deep technical partnership for IoT antenna integration",
        "Murata (premium/innovation): Technology partnership for advanced antenna modules and AiP solutions"
    ]
    for s in suppliers:
        story.append(Paragraph(f"• {s}", styles['BulletText']))

    story.append(Paragraph("<b>Industry Partnerships:</b>", styles['H3Header']))
    industry = [
        "ZVEI (German Electrical and Electronics Manufacturers Association)",
        "Regional robotics clusters and university research centers (TUM, KIT)",
        "RF simulation software partnerships (Keysight, CST Studio)"
    ]
    for i in industry:
        story.append(Paragraph(f"• {i}", styles['BulletText']))

    story.append(Spacer(1, 15))

    # 6. Pricing Strategy
    story.append(Paragraph("6. Pricing and Margin Strategy", styles['SubsectionHeader']))

    pricing_data = [
        [Paragraph('<b>Customer Type</b>', styles['TableHeader']),
         Paragraph('<b>Volume</b>', styles['TableHeader']),
         Paragraph('<b>Discount</b>', styles['TableHeader']),
         Paragraph('<b>Margin</b>', styles['TableHeader']),
         Paragraph('<b>Service Level</b>', styles['TableHeader'])],
        ['Large OEM (>50k units/yr)', '50,000+', '25-35%', '20-25%', 'Full tech support, dedicated account'],
        ['Mid-size integrator', '5,000-20,000', '15-20%', '30-35%', 'Technical support, training'],
        ['Small integrator/reseller', '<5,000', '5-10%', '35-45%', 'Standard support, online resources'],
        ['Direct project-based', 'Per project', '10-20%', '40-55%', 'Full engineering services'],
    ]

    pricing_table = Table(pricing_data, colWidths=[100, 70, 60, 55, 165])
    pricing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PremiumColors.NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), PremiumColors.WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [PremiumColors.WHITE, PremiumColors.GRAY_100]),
        ('GRID', (0, 0), (-1, -1), 0.5, PremiumColors.GRAY_200),
    ]))
    story.append(pricing_table)
    story.append(Spacer(1, 15))

    # 7. Marketing
    story.append(Paragraph("7. Marketing and Brand Positioning", styles['SubsectionHeader']))

    positioning_text = """<b>Core Positioning:</b> "The trusted German antenna solutions partner for autonomous
    systems and Industrial 4.0 – combining global supply chain reach with local engineering expertise.\""""
    story.append(Paragraph(positioning_text, styles['PremiumBody']))

    story.append(Paragraph("<b>Key Messages:</b>", styles['H3Header']))
    messages = [
        "Engineering Excellence: German engineering heritage applied to modern antenna challenges",
        "Vertical Expertise: Deep understanding of robotics, automation, and autonomous systems",
        "Local Advantage: Proximity to major manufacturing clusters; rapid response",
        "Future-Proof Solutions: Portfolio addressing today's 5G and tomorrow's 6G evolution"
    ]
    for m in messages:
        story.append(Paragraph(f"• {m}", styles['BulletText']))

    # Marketing budget table
    story.append(Spacer(1, 10))
    marketing_data = [
        [Paragraph('<b>Channel</b>', styles['TableHeader']),
         Paragraph('<b>Investment</b>', styles['TableHeader']),
         Paragraph('<b>Focus</b>', styles['TableHeader'])],
        ['Digital/SEO/SEM', '€80,000/yr', 'Lead generation for targeted keywords'],
        ['Trade Shows', '€60,000/yr', 'HANNOVER MESSE, AUTOMATICA, LogiMAT'],
        ['Technical Content', '€40,000/yr', 'Whitepapers, case studies, webinars'],
        ['Industry Sponsorship', '€50,000/yr', 'ZVEI, DIN committees, robotics consortia'],
        ['Direct Account Mgmt', '€150,000/yr', 'Key account development'],
        ['Total Budget', '€380,000/yr', ''],
    ]

    mkt_table = Table(marketing_data, colWidths=[130, 90, 230])
    mkt_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PremiumColors.GOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), PremiumColors.NAVY_DARK),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [PremiumColors.WHITE, PremiumColors.GRAY_100]),
        ('GRID', (0, 0), (-1, -1), 0.5, PremiumColors.GRAY_200),
        ('BACKGROUND', (0, -1), (-1, -1), PremiumColors.NAVY_LIGHT),
        ('TEXTCOLOR', (0, -1), (-1, -1), PremiumColors.WHITE),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(mkt_table)

    story.append(PageBreak())
    return story

def build_risk_analysis(styles):
    """Builds the risk analysis section"""
    story = []

    story.append(ChapterHeader(7, "Risk Analysis and Mitigation", 450))
    story.append(Spacer(1, 20))

    intro_text = """A comprehensive risk management framework is essential for navigating the dynamic
    antenna market. The following analysis identifies key risks and provides mitigation strategies."""
    story.append(Paragraph(intro_text, styles['PremiumBody']))
    story.append(Spacer(1, 15))

    risks = [
        ("Risk 1: Supply Chain Disruptions", "HIGH",
         "Component shortages leading to delivery delays and revenue loss.",
         "Maintain dual-source relationships; establish safety stock; develop secondary supplier relationships with Tier 2 manufacturers."),
        ("Risk 2: Aggressive Price Competition", "MEDIUM",
         "Margin compression from low-cost Asian competitors (Huawei, ZTT).",
         "Differentiate through value-added services; target premium market segments less price-sensitive."),
        ("Risk 3: Rapid Technology Obsolescence", "MEDIUM",
         "Inventory write-offs if antenna technology standards shift unexpectedly.",
         "Active monitoring of standards development (3GPP, IEEE 802.11); focus on broad multi-band solutions."),
        ("Risk 4: Regulatory Changes", "LOW",
         "Sudden spectrum band reallocation could eliminate market segments.",
         "Maintain awareness of European spectrum policy; diversify portfolio across multiple frequency bands."),
        ("Risk 5: Customer Concentration", "MEDIUM",
         "Over-reliance on 1-2 large customers creating vulnerability.",
         "Diversify customer base across verticals; develop long-term contracts with key accounts."),
        ("Risk 6: Competitive Response", "MEDIUM",
         "Kathrein or other European competitors may enter same verticals with superior resources.",
         "Establish market position early in 2026; develop defensible niches through application expertise.")
    ]

    # Create risk matrix style presentation
    for title, severity, impact, mitigation in risks:
        # Risk header with severity color
        if severity == "HIGH":
            sev_color = '#DC2626'
        elif severity == "MEDIUM":
            sev_color = '#C9A227'
        else:
            sev_color = '#059669'

        story.append(Paragraph(f"<b>{title}</b> <font color='{sev_color}'>[{severity} RISK]</font>", styles['H3Header']))
        story.append(Paragraph(f"<b>Impact:</b> {impact}", styles['PremiumBody']))
        story.append(Paragraph(f"<b>Mitigation:</b> {mitigation}", styles['PremiumBody']))
        story.append(Spacer(1, 10))

    story.append(PageBreak())
    return story

def build_implementation_timeline(styles):
    """Builds the implementation timeline section"""
    story = []

    story.append(ChapterHeader(8, "Implementation Timeline", 450))
    story.append(Spacer(1, 20))

    timeline_data = [
        ("Q1 2026 (January-March)", "FOUNDATION", [
            "Supplier relationship establishment (Amphenol, Taoglas, Murata)",
            "Product portfolio definition: Finalize Tier A/B/C offerings",
            "Sales team recruitment: 2-3 senior sales engineers",
            "Technical capability: RF lab planning and initial equipment procurement",
            "Market research completion: Refine vertical market assessments"
        ], "Supplier agreements in place; core team assembled; product roadmap finalized"),

        ("Q2 2026 (April-June)", "LAUNCH", [
            "Market launch: Announce product offerings, establish digital presence",
            "HANNOVER MESSE participation: Exhibit at Germany's largest industrial trade show",
            "First customer projects: Secure 3-5 initial customers (pilot projects)",
            "Training and certification: RF engineers complete advanced training",
            "Partnership outreach: Engage 10-15 potential channel partners"
        ], "Market presence established; initial customer references secured"),

        ("Q3 2026 (July-September)", "SCALE", [
            "AUTOMATICA participation: Showcase at automation/robotics trade show",
            "Vertical deepening: Develop vertical-specific case studies",
            "RF lab operational: Antenna measurement and testing capability live",
            "Channel expansion: Onboard 5-8 channel partners",
            "Technical content launch: White papers, webinars on antenna selection"
        ], "Technical credibility established; channel network emerging"),

        ("Q4 2026 (October-December)", "OPTIMIZE", [
            "Year-end sales push: Accelerate key account acquisition",
            "2027 planning: Assess performance, refine strategy based on market feedback",
            "Product expansion: Launch Tier B solutions (26 GHz, MIMO)",
            "Partnership deepening: Formalize exclusive arrangements",
            "Team scaling: Plan 2027 hiring (additional sales, technical staff)"
        ], "Full-year revenue targets achieved; 2027 growth foundation established"),
    ]

    for quarter, phase, activities, outcome in timeline_data:
        story.append(Paragraph(f"<b>{quarter}</b> <font color='#C9A227'>[{phase}]</font>", styles['SubsectionHeader']))

        for activity in activities:
            story.append(Paragraph(f"• {activity}", styles['BulletText']))

        story.append(Paragraph(f"<b>Target Outcome:</b> {outcome}", styles['InsightText']))
        story.append(Spacer(1, 15))

    story.append(PageBreak())
    return story

def build_success_metrics(styles):
    """Builds the success metrics and KPIs section"""
    story = []

    story.append(ChapterHeader(9, "Success Metrics and KPIs", 450))
    story.append(Spacer(1, 20))

    # Key metrics boxes
    metrics_row1 = [
        [
            KeyMetricBox("€8.5-10.5M", "2026 Revenue Target", accent_color=PremiumColors.TEAL),
            KeyMetricBox("35-40%", "Gross Margin Target", accent_color=PremiumColors.GOLD),
            KeyMetricBox("12-18%", "EBITDA Margin", accent_color=PremiumColors.CHART_3),
            KeyMetricBox("25-35%", "YoY Growth (2027)", accent_color=PremiumColors.CHART_4)
        ]
    ]

    metrics_table1 = Table(metrics_row1, colWidths=[125, 125, 125, 125])
    metrics_table1.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(metrics_table1)
    story.append(Spacer(1, 25))

    # Financial Metrics
    story.append(Paragraph("Financial Metrics (2026 Target)", styles['SubsectionHeader']))

    financial = [
        "Total Revenue: €8.5-10.5 million",
        "Gross Margin: 35-40%",
        "EBITDA Margin: 12-18% (after operating expenses)",
        "Revenue Growth (YoY 2027): 25-35%",
        "Customer Acquisition Cost: <€5,000 per customer (direct) / <€2,000 per customer (channel)",
        "Customer Lifetime Value: >€100,000 (estimated based on 5-year relationship)"
    ]
    for f in financial:
        story.append(Paragraph(f"• {f}", styles['BulletText']))

    story.append(Spacer(1, 15))

    # Operational Metrics
    story.append(Paragraph("Operational Metrics", styles['SubsectionHeader']))

    operational = [
        "On-time Delivery Rate: >95%",
        "Customer Satisfaction Score (NPS): >50",
        "Technical Support Response Time: <4 hours (critical), <24 hours (standard)",
        "Product Portfolio Breadth: >50 SKUs covering major applications",
        "Supplier Relationship Score: Strong partnerships with 3+ Tier 1 suppliers"
    ]
    for o in operational:
        story.append(Paragraph(f"• {o}", styles['BulletText']))

    story.append(Spacer(1, 15))

    # Market Metrics
    story.append(Paragraph("Market Metrics", styles['SubsectionHeader']))

    market = [
        "Market Share in Target Verticals: 3-5% German market by end-2026",
        "Customer Count: 50-80 direct customers; 20-30 channel partners",
        "Vertical Revenue Mix: 35% warehouse/logistics, 30% industrial IoT, 25% autonomous systems, 10% drones",
        "Win Rate vs. Competitors: >25% on bid opportunities"
    ]
    for m in market:
        story.append(Paragraph(f"• {m}", styles['BulletText']))

    story.append(Spacer(1, 15))

    # Strategic Metrics
    story.append(Paragraph("Strategic Metrics", styles['SubsectionHeader']))

    strategic = [
        "Thought Leadership: 2-3 speaking engagements at major conferences",
        "Industry Recognition: Membership/participation in ZVEI, 3GPP vertical groups",
        "Innovation Pipeline: 5-8 new product introductions annually",
        "Partnership Ecosystem: 3+ strategic technology partnerships"
    ]
    for s in strategic:
        story.append(Paragraph(f"• {s}", styles['BulletText']))

    story.append(PageBreak())
    return story

def build_conclusion(styles):
    """Builds the conclusion section"""
    story = []

    story.append(ChapterHeader(10, "Conclusion", 450))
    story.append(Spacer(1, 20))

    conclusion_text1 = """The global antenna market for IoT and autonomous systems presents extraordinary
    growth opportunities for German distributors and systems integrators in 2026 and beyond. The combination of
    rapid 5G rollout with harmonized European spectrum, Industry 4.0 digital transformation mandates, explosive
    growth in robotics and commercial drones, and increasing sophistication of antenna technology creates a
    favorable backdrop for market entry and rapid scaling."""
    story.append(Paragraph(conclusion_text1, styles['PremiumBody']))

    story.append(Spacer(1, 15))

    conclusion_text2 = """However, success requires moving beyond pure component distribution toward integrated
    solutions, technical consulting, and application-specific expertise. The German distributor's competitive
    advantage lies in engineering and systems integration capabilities, local presence in manufacturing-concentrated
    regions, understanding of regulatory frameworks, and alignment with Industry 4.0 and sustainability priorities."""
    story.append(Paragraph(conclusion_text2, styles['PremiumBody']))

    story.append(Spacer(1, 15))

    # Key takeaway callout
    callout_text = """\"By following the strategic recommendations outlined in this report, a German antenna
    distributor can establish market leadership and capture significant share of the <b>€8-12 billion annual
    market opportunity</b> in IoT and autonomous systems connectivity by 2028.\""""
    story.append(Paragraph(callout_text, styles['Callout']))

    story.append(Spacer(1, 15))

    # Final emphasis
    final_text = """<b>The window for market positioning is 2026.</b> The companies establishing credibility,
    customer relationships, and technical depth in this year will define the competitive landscape for the
    remainder of the decade."""
    story.append(Paragraph(final_text, styles['PremiumBody']))

    story.append(PageBreak())
    return story

def build_references(styles):
    """Builds the references section"""
    story = []

    story.append(Paragraph("References", styles['SectionHeader']))
    story.append(Spacer(1, 15))

    references = [
        "[1] IoT Antennas in Electronic Devices Market 2026: Growth Potential and Strategic Opportunities. LinkedIn Pulse, December 2025.",
        "[2] Autonomous Mobile Robots (AMR) Market Analysis. MarketsandMarkets, November 2025.",
        "[3] IoT Analytics. Number of Connected IoT Devices Growing 14% to 21.1 Billion. December 2024.",
        "[4] Drone Tracking Antenna Market Growth 2025–2033 Forecast. LinkedIn Pulse, September 2025.",
        "[5] Germany Warehouse Robotics Market: Size, Share & Growth Analysis. Verified Market Research, June 2025.",
        "[6] Radio Spectrum Policy Group Opinion on 5G Developments and 6G Spectrum. EU RSPG, October 2023.",
        "[7] Phased Array Antenna Market Growth Outlook with AI Innovations. LinkedIn Pulse, December 2025.",
        "[8] Germany Drone Regulations and Autonomous Systems Framework. EASA/German Aviation Act.",
        "[9] Global Antenna Market Size, Share, Trends, Growth & Forecast. Mordor Intelligence, October 2025.",
        "[10] World Antenna Market Landscape: 2024-2032 Analysis. Allied Market Research.",
        "[11] Autonomous Mobile Robots Market Analysis. FactMR, September 2025.",
        "[12] Germany Industrial IoT Software Market: AI and Automation Impact. LinkedIn Pulse, December 2025.",
        "[13] 5G Support for Industrial IoT Applications. PubMed Central/NIH, 2020.",
        "[14] DIGITALEUROPE 5G Spectrum Recommendations. January 2019.",
        "[15] 5G Industrial IoT Demand 2026: Size & Market White Spaces. LinkedIn Pulse, December 2025.",
        "[16] 5G mmWave Antenna Module Strategic Insights. Archive Market Research, May 2024.",
        "[17] Next-Generation Antenna-Based Wireless Technologies Market Analysis. Data-Alliance, October 2025.",
        "[18] Autonomous Aerial Robot Market Global Analysis. Future Market Insights, October 2025.",
        "[19] Autonomous Navigation Market Size, Share & Forecast. Allied Market Research, April 2025.",
        "[20] MmWave Phased Array Antenna Module Market Report. Lucintel.",
        "[21] Top Passive Cellular Antenna Vendors 2025. ABI Research, August 2025.",
        "[22] Defense Integrated Antenna Market Size, Share & Growth. ResearchNester, September 2025.",
        "[23] Germany Police Authority to Neutralize Drones. Reuters, October 2025.",
    ]

    ref_style = ParagraphStyle(
        name='Reference',
        fontName='Helvetica',
        fontSize=8,
        textColor=PremiumColors.GRAY_700,
        spaceAfter=4,
        leading=10
    )

    for ref in references:
        story.append(Paragraph(ref, ref_style))

    story.append(Spacer(1, 30))

    # Document info
    story.append(Paragraph("<b>Document Information</b>", styles['H3Header']))
    doc_info = """
    <b>Prepared for:</b> German IoT Components Distributor & Systems Integrator<br/>
    <b>Prepared by:</b> Crimson Sun Technologies (An Interstates & Vagabonds Company)<br/>
    <b>Report Date:</b> December 2025<br/>
    <b>Classification:</b> Strategic Planning Document - Confidential<br/>
    <b>Validity Period:</b> 2026 Planning Cycle (Q1-Q4 2026)
    """
    story.append(Paragraph(doc_info, styles['PremiumBody']))

    return story

# ============================================================================
# MAIN DOCUMENT BUILDER
# ============================================================================

def add_chart_to_story(story, chart_func, width, height, caption, styles):
    """Helper to add a chart to the story"""
    chart_buf = chart_func()
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp.write(chart_buf.read())
        tmp_path = tmp.name
    story.append(Spacer(1, 15))
    story.append(Image(tmp_path, width=width, height=height))
    story.append(Paragraph(caption, styles['Caption']))
    story.append(Spacer(1, 10))

def build_premium_report(output_path):
    """Builds the complete premium report"""

    # Create document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=60
    )

    # Get styles
    styles = get_premium_styles()

    # Build story (content)
    story = []

    # Cover page will be added separately via onFirstPage
    story.append(PageBreak())

    # Table of Contents
    story.extend(build_toc(styles))

    # Executive Summary
    story.extend(build_executive_summary(styles))

    # Market Overview
    story.extend(build_market_overview(styles))

    # Add market growth chart after market overview
    add_chart_to_story(story, create_market_growth_chart, 450, 250,
                      "Figure 1: Antenna Market Growth Projections by Segment (2024-2030)", styles)

    story.append(PageBreak())

    # Technology Trends
    story.extend(build_technology_trends(styles))

    # Add CAGR comparison chart
    add_chart_to_story(story, create_cagr_comparison_chart, 450, 250,
                      "Figure 2: Growth Rates Comparison Across Key Market Segments", styles)

    # Competitive Landscape
    story.extend(build_competitive_landscape(styles))

    # Add regional chart
    add_chart_to_story(story, create_regional_market_chart, 350, 230,
                      "Figure 3: Global Antenna Market Distribution by Region (2025)", styles)

    # Regional Insights
    story.extend(build_regional_insights(styles))

    # Add Germany market chart
    add_chart_to_story(story, create_germany_market_chart, 450, 250,
                      "Figure 4: Germany Key Market Segments Growth Projection", styles)

    # Strategic Recommendations
    story.extend(build_strategic_recommendations(styles))

    # Add portfolio chart before risk section
    add_chart_to_story(story, create_portfolio_allocation_chart, 300, 300,
                      "Figure 5: Recommended Product Portfolio Allocation", styles)

    # Risk Analysis
    story.extend(build_risk_analysis(styles))

    # Implementation Timeline
    story.extend(build_implementation_timeline(styles))

    # Add timeline chart
    add_chart_to_story(story, create_timeline_chart, 480, 180,
                      "Figure 6: 2026 Implementation Roadmap", styles)

    # Success Metrics
    story.extend(build_success_metrics(styles))

    # Conclusion
    story.extend(build_conclusion(styles))

    # References
    story.extend(build_references(styles))

    # Build PDF
    doc.build(
        story,
        onFirstPage=create_cover_page,
        onLaterPages=page_header_footer
    )

    print(f"Premium report generated: {output_path}")
    return output_path

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    output_dir = "/Users/philippholke/Crimson Sun/bane/output"
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "Global_IoT_Robotics_Antenna_Market_Strategy_2026_Premium.pdf")
    build_premium_report(output_file)
