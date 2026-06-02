from django.contrib import admin
from .models import (
    Category, Department, Level, Term, Book, Rating,
    Membership, BorrowRequest
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('name',)

class RatingInline(admin.TabularInline):
    model = Rating
    extra = 0
    readonly_fields = ('user', 'rating', 'comment', 'created')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'department', 'level', 'term', 'price', 'stock', 'available', 'created')
    list_filter = ('available', 'category', 'department', 'level', 'term')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [RatingInline]



@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'created')
    list_filter = ('rating', 'created')

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "is_active_flag", "start_date", "end_date", "borrow_limit", "fine_balance")

    def is_active_flag(self, obj):
        return obj.status == "active"
    is_active_flag.boolean = True
    is_active_flag.short_description = "Active"


@admin.register(BorrowRequest)
class BorrowRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'status', 'request_date', 'return_date')
    list_filter = ('status',)
