from django.urls import path
from . import views

app_name = 'lib'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('', views.home, name='home'),
    path('profile/', views.student_dashboard, name='student_dashboard'),


    path('books/', views.book_list, name='book_list'),
    path('books/category/<slug:category_slug>/', views.book_list, name='book_list_by_category'),
    path('books/department/<int:dept_id>/', views.book_list, name='book_list_by_department'),
    path('books/level/<int:level_id>/', views.book_list, name='book_list_by_level'),
    path('books/term/<int:term_id>/', views.book_list, name='book_list_by_term'),
    path('book/<slug:slug>/', views.book_detail, name='book_detail'),

    path('rate/<int:book_id>/', views.rate_book, name='rate_book'),

  
    path('membership/', views.request_membership, name='membership'),
    path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('librarian/', views.librarian_dashboard, name='librarian_dashboard'),
    path('librarian/membership/<int:membership_id>/approve/',
         views.approve_membership, name='approve_membership'),
    path('librarian/membership/<int:membership_id>/reject/',
         views.reject_membership, name='reject_membership'),

    path('request/approve/<int:req_id>/', views.approve_borrow, name='approve_borrow'),
    path('request/decline/<int:req_id>/', views.decline_borrow, name='decline_borrow'),
    path('request/cancel/<int:req_id>/', views.cancel_borrow_request, name='cancel_borrow'),
    
    path('librarian/books/add/', views.book_create, name='book_create'),
    path('librarian/books/<int:book_id>/edit/', views.book_edit, name='book_edit'),
    path('librarian/books/<int:book_id>/delete/', views.book_delete, name='book_delete'),
    

    path('librarian/return/', views.process_return, name='process_return'),
    path('librarian/user/<int:user_id>/history/', views.user_history, name='user_history'),
    path('librarian/users/', views.users_overview, name='users_overview'),
    path('my_profile/', views.my_profile, name='my_profile'),
    path("chat-api/", views.chat_api, name="chat_api"),


    

]
