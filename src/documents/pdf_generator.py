"""
PDF Generator
============
Generate PDFs for packing slips, storage labels, invoices, etc.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from io import BytesIO

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class DocumentType(Enum):
    """Document types"""
    PACKING_SLIP = "packing_slip"
    STORAGE_LABEL = "storage_label"
    INVOICE = "invoice"
    PICK_LIST = "pick_list"


class PDFGenerator:
    """Generate PDF documents"""
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Install with: pip install reportlab"
            )
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#555555'),
            spaceAfter=8
        ))
    
    def generate_packing_slip(
        self,
        listing: Dict[str, Any],
        buyer_info: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> BytesIO:
        """Generate packing slip PDF"""
        buffer = BytesIO() if not output_path else None
        doc = SimpleDocTemplate(
            output_path or buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        story = []
        
        # Title
        story.append(Paragraph("PACKING SLIP", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Order info
        order_data = [
            ['Order Date:', listing.get('sold_date', datetime.now().strftime('%Y-%m-%d'))],
            ['Order Number:', str(listing.get('id', ''))],
            ['Platform:', listing.get('sold_platform', 'N/A')],
        ]
        
        order_table = Table(order_data, colWidths=[2*inch, 4*inch])
        order_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(order_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Shipping address
        story.append(Paragraph("SHIP TO:", self.styles['CustomHeading']))
        shipping_address = buyer_info.get('shipping_address', {})
        address_lines = [
            buyer_info.get('buyer_name', 'N/A'),
            shipping_address.get('address_line1', ''),
            shipping_address.get('address_line2', ''),
            f"{shipping_address.get('city', '')}, {shipping_address.get('state', '')} {shipping_address.get('zip', '')}",
            shipping_address.get('country', 'USA')
        ]
        
        for line in address_lines:
            if line:
                story.append(Paragraph(line, self.styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Item details
        story.append(Paragraph("ITEM DETAILS:", self.styles['CustomHeading']))
        item_data = [
            ['Title:', listing.get('title', 'N/A')],
            ['SKU:', listing.get('sku', 'N/A')],
            ['Storage Location:', listing.get('storage_location', 'N/A')],
            ['Quantity:', str(listing.get('quantity', 1))],
        ]
        
        item_table = Table(item_data, colWidths=[2*inch, 4*inch])
        item_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(item_table)
        
        # Build PDF
        doc.build(story)
        
        if buffer:
            buffer.seek(0)
            return buffer
        return None
    
    def generate_storage_label(
        self,
        listing: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> BytesIO:
        """Generate storage label PDF"""
        buffer = BytesIO() if not output_path else None
        doc = SimpleDocTemplate(
            output_path or buffer,
            pagesize=(4*inch, 2*inch),  # Small label size
            rightMargin=0.1*inch,
            leftMargin=0.1*inch,
            topMargin=0.1*inch,
            bottomMargin=0.1*inch
        )
        
        story = []
        
        # Storage location (large)
        location_style = ParagraphStyle(
            name='LocationStyle',
            fontSize=24,
            textColor=colors.HexColor('#000000'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph(
            listing.get('storage_location', 'N/A'),
            location_style
        ))
        
        story.append(Spacer(1, 0.1*inch))
        
        # Title (smaller)
        title_style = ParagraphStyle(
            name='TitleStyle',
            fontSize=8,
            textColor=colors.HexColor('#333333'),
            alignment=TA_CENTER
        )
        title = listing.get('title', 'N/A')
        if len(title) > 40:
            title = title[:37] + '...'
        story.append(Paragraph(title, title_style))
        
        # SKU if available
        if listing.get('sku'):
            sku_style = ParagraphStyle(
                name='SKUStyle',
                fontSize=7,
                textColor=colors.HexColor('#666666'),
                alignment=TA_CENTER
            )
            story.append(Spacer(1, 0.05*inch))
            story.append(Paragraph(f"SKU: {listing['sku']}", sku_style))
        
        # Build PDF
        doc.build(story)
        
        if buffer:
            buffer.seek(0)
            return buffer
        return None
    
    def generate_pick_list(
        self,
        listings: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> BytesIO:
        """Generate pick list PDF for multiple items"""
        buffer = BytesIO() if not output_path else None
        doc = SimpleDocTemplate(
            output_path or buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        story = []
        
        # Title
        story.append(Paragraph("PICK LIST", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Items table
        table_data = [['#', 'Storage', 'Title', 'SKU', 'Qty']]
        
        for idx, listing in enumerate(listings, 1):
            title = listing.get('title', 'N/A')
            if len(title) > 50:
                title = title[:47] + '...'
            table_data.append([
                str(idx),
                listing.get('storage_location', 'N/A'),
                title,
                listing.get('sku', 'N/A'),
                str(listing.get('quantity', 1))
            ])
        
        items_table = Table(table_data, colWidths=[0.5*inch, 1*inch, 3.5*inch, 1*inch, 0.5*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(items_table)
        
        # Build PDF
        doc.build(story)
        
        if buffer:
            buffer.seek(0)
            return buffer
        return None

