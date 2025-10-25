from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AfipConfig, Invoice, InvoiceItem


@admin.register(AfipConfig)
class AfipConfigAdmin(admin.ModelAdmin):
    list_display = [
        'hotel', 'cuit', 'tax_condition', 'point_of_sale', 
        'environment', 'is_active', 'last_invoice_number'
    ]
    list_filter = ['environment', 'is_active', 'tax_condition']
    search_fields = ['hotel__name', 'cuit']
    readonly_fields = ['last_invoice_number', 'last_cae_date', 'created_at', 'updated_at', 'afip_token', 'afip_sign', 'afip_token_generation', 'afip_token_expiration']
    
    fieldsets = (
        ('Hotel', {
            'fields': ('hotel',)
        }),
        ('Datos Fiscales', {
            'fields': ('cuit', 'tax_condition', 'point_of_sale')
        }),
        ('Certificados', {
            'fields': ('certificate_path', 'private_key_path')
        }),
        ('Configuración', {
            'fields': ('environment', 'is_active')
        }),
        ('WSAA Token', {
            'fields': ('afip_token', 'afip_sign', 'afip_token_generation', 'afip_token_expiration'),
            'classes': ('collapse',)
        }),
        ('Control de Numeración', {
            'fields': ('last_invoice_number', 'last_cae_date'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        })
    )


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    fields = ['description', 'quantity', 'unit_price', 'subtotal', 'vat_rate', 'vat_amount', 'total']
    readonly_fields = ['subtotal', 'vat_amount', 'total']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'number', 'hotel', 'type', 'status', 'total', 
        'issue_date', 'cae_status', 'created_at'
    ]
    list_filter = [
        'status', 'type', 'hotel', 'issue_date', 'created_at'
    ]
    search_fields = [
        'number', 'hotel__name', 'client_name', 'client_document_number', 'cae'
    ]
    readonly_fields = [
        'id', 'number', 'cae', 'cae_expiration', 'created_at', 
        'updated_at', 'sent_to_afip_at', 'approved_at', 'retry_count'
    ]
    
    fieldsets = (
        ('Identificación', {
            'fields': ('id', 'number', 'type', 'status')
        }),
        ('Relaciones', {
            'fields': ('hotel', 'reservation', 'payment')
        }),
        ('Fechas', {
            'fields': ('issue_date', 'cae_expiration')
        }),
        ('Montos', {
            'fields': ('net_amount', 'vat_amount', 'total', 'currency')
        }),
        ('Datos del Cliente', {
            'fields': (
                'client_name', 'client_document_type', 'client_document_number',
                'client_tax_condition', 'client_address'
            )
        }),
        ('CAE y AFIP', {
            'fields': ('cae', 'afip_response'),
            'classes': ('collapse',)
        }),
        ('Archivos', {
            'fields': ('pdf_file', 'pdf_url'),
            'classes': ('collapse',)
        }),
        ('Control', {
            'fields': ('retry_count', 'last_error', 'sent_to_afip_at', 'approved_at'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [InvoiceItemInline]
    
    def cae_status(self, obj):
        """Muestra el estado del CAE"""
        if not obj.cae:
            return format_html('<span style="color: red;">Sin CAE</span>')
        
        if obj.is_expired():
            return format_html('<span style="color: red;">CAE Expirado</span>')
        
        if obj.is_approved():
            return format_html('<span style="color: green;">CAE Válido</span>')
        
        return format_html('<span style="color: orange;">Pendiente</span>')
    
    cae_status.short_description = 'Estado CAE'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('hotel', 'reservation', 'payment')


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = [
        'invoice', 'description', 'quantity', 'unit_price', 
        'subtotal', 'vat_amount', 'total'
    ]
    list_filter = ['invoice__hotel', 'invoice__type']
    search_fields = ['description', 'invoice__number']
    readonly_fields = ['subtotal', 'vat_amount', 'total']
    
    fieldsets = (
        ('Item', {
            'fields': ('invoice', 'description', 'afip_code')
        }),
        ('Cantidad y Precio', {
            'fields': ('quantity', 'unit_price')
        }),
        ('Cálculos', {
            'fields': ('subtotal', 'vat_rate', 'vat_amount', 'total'),
            'classes': ('collapse',)
        })
    )
