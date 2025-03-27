from django.contrib import admin
from .models import Book, Category, Loan, Review, ActivityLog

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'quantity', 'available', 'is_available')
    list_filter = ('categories', 'created_at')
    search_fields = ('title', 'author', 'isbn')
    filter_horizontal = ('categories',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'isbn', 'description')
        }),
        ('Inventory', {
            'fields': ('quantity', 'available')
        }),
        ('Metadata', {
            'fields': ('categories', 'publication_date', 'cover_image')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

class LoanAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'checkout_date', 'due_date', 'status', 'is_overdue')
    list_filter = ('status', 'checkout_date', 'due_date')
    search_fields = ('book__title', 'user__username')
    readonly_fields = ('checkout_date',)
    date_hierarchy = 'due_date'

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('book__title', 'user__username', 'comment')
    readonly_fields = ('created_at', 'updated_at')

class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'details')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

admin.site.register(Category, CategoryAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Loan, LoanAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(ActivityLog, ActivityLogAdmin)
