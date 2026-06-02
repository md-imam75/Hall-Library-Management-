from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User 
from django.contrib import messages
from django.db.models import Q, Avg, Min, Max,Count
from django.utils import timezone
from django.http import JsonResponse
from .recommender import recommend_for_user
from datetime import timedelta
from .models import (
    Book, Category, Department, Level, Term, Rating,
    Membership, BorrowRequest,  Profile
)
from .forms import RegistrationForm, RatingForm, BookForm, ReturnForm, ProfileUpdateForm,UserUpdateForm
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.forms import ModelForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .utils import is_cuet_student_email
from django.views.decorators.http import require_POST
@staff_member_required
def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book added successfully.')
            return redirect('lib:librarian_dashboard')
    else:
        form = BookForm()
    return render(request, 'lib/book_form.html', {
        'form': form,
        'mode': 'create',
    })

@staff_member_required
def book_edit(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book updated successfully.')
            return redirect('lib:librarian_dashboard')
    else:
        form = BookForm(instance=book)
    return render(request, 'lib/book_form.html', {
        'form': form,
        'mode': 'edit',
        'book': book,
    })

@staff_member_required
def book_delete(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Book deleted successfully.')
        return redirect('lib:librarian_dashboard')
    return render(request, 'lib/book_confirm_delete.html', {
        'book': book,
    })

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            if user.is_staff:
                return redirect('lib:librarian_dashboard')
            else:
                return redirect('lib:student_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'lib/login.html')

    return render(request, 'lib/login.html')


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Authenticate the newly created user so the user object has a
            # backend attribute required by django.contrib.auth.login when
            # multiple authentication backends are configured.
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1') if 'password1' in form.cleaned_data else None
            auth_user = None
            if username and password:
                auth_user = authenticate(request, username=username, password=password)
            if auth_user is not None:
                login(request, auth_user)
            else:
                # Fallback: set backend explicitly (ModelBackend is commonly used).
                # This is safe when the default backend is Django's ModelBackend.
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
            messages.success(request, 'Registration successful.')
            return redirect('lib:login')
    else:
        form = RegistrationForm()
    return render(request, 'lib/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('lib:login')

def home(request):
    featured_books = Book.objects.filter(available=True).order_by('-created')[:8]
    categories = Category.objects.all()
    return render(request, 'lib/home.html', {'featured_books': featured_books, 'categories': categories})

def book_list(request, category_slug=None, dept_id=None, level_id=None, term_id=None):
    category = None
    categories = Category.objects.all()
    departments = Department.objects.all()
    levels = Level.objects.all()
    terms = Term.objects.all()
    books = Book.objects.filter(available=True)

    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        books = books.filter(category=category)
    if dept_id:
        dept = get_object_or_404(Department, id=dept_id)
        books = books.filter(department=dept)
    if level_id:
        level = get_object_or_404(Level, id=level_id)
        books = books.filter(level=level)
    if term_id:
        term = get_object_or_404(Term, id=term_id)
        books = books.filter(term=term)

    search_q = request.GET.get('search')
    if search_q:
        books = books.filter(
            Q(title__icontains=search_q) |
            Q(author__icontains=search_q) |
            Q(description__icontains=search_q)
        )

    dept_q = request.GET.get('department')
    if dept_q:
        books = books.filter(department_id=dept_q)

    level_q = request.GET.get('level')
    if level_q:
        books = books.filter(level_id=level_q)

    term_q = request.GET.get('term')
    if term_q:
        books = books.filter(term_id=term_q)

    return render(request, 'lib/book_list.html', {
        'books': books,
        'categories': categories,
        'departments': departments,
        'levels': levels,
        'terms': terms,
    })


def book_detail(request, slug):
    book = get_object_or_404(Book, slug=slug, available=True)
    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(user=request.user, book=book)
        except Rating.DoesNotExist:
            user_rating = None
    rating_form = RatingForm(instance=user_rating)
    related_books = (
        Book.objects
        .filter(department=book.department) 
        .exclude(pk=book.pk)                
        [:6]                                
    )
    return render(request, 'lib/book_detail.html', {
        'book': book,
        'related_books': related_books,
        'user_rating': user_rating,
        'rating_form': rating_form,
        'related_books': related_books,
    })

@login_required
def rate_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    borrowed_items = BorrowRequest.objects.filter(user=request.user, book=book, status='returned')
    if not (borrowed_items.exists()):
        messages.error(request, 'You can only rate books you have borrowed.')
        return redirect('lib:book_detail', slug=book.slug)
    try:
        rating = Rating.objects.get(user=request.user, book=book)
    except Rating.DoesNotExist:
        rating = None
    if request.method == 'POST':
        form = RatingForm(request.POST, instance=rating)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.user = request.user
            rating.book = book
            rating.save()
            messages.success(request, 'Your rating has been submitted.')
            return redirect('lib:book_detail', slug=book.slug)
    else:
        form = RatingForm(instance=rating)
    return render(request, 'lib/rate_book.html', {'form': form, 'book': book})

@login_required
def request_membership(request):
    # Block staff; only students use this screen
    if request.user.is_staff:
        return redirect("lib:librarian_dashboard")

    membership = Membership.objects.filter(user=request.user).first()

    # If already active and not expired → just show info
    today = timezone.now().date()
    if membership and membership.status == "active" and membership.end_date and membership.end_date >= today:
        messages.info(request, "You already have an active membership.")
        return render(request, "lib/membership.html", {"membership": membership})

    if request.method == "POST":
        # 1. Check CUET email
        email = request.user.email or ""
        if not is_cuet_student_email(email):
            messages.error(request, "Your account email must be a CUET student email (xxx@student.cuet.ac.bd).")
            return redirect("lib:membership")

        # 2. Check student ID card upload
        student_card = request.FILES.get("student_card")
        if not student_card:
            messages.error(request, "Please upload your student ID card image.")
            return redirect("lib:membership")

        # 3. Create or update membership as pending 1-year request
        start_date = today
        end_date = today + timedelta(days=365)
        borrow_limit = 50

        if membership is None:
            membership = Membership.objects.create(
                user=request.user,
                status="pending",
                start_date=start_date,
                end_date=end_date,
                borrow_limit=borrow_limit,
                student_card=student_card,
            )
        else:
            membership.status = "pending"
            membership.start_date = start_date
            membership.end_date = end_date
            membership.borrow_limit = borrow_limit
            membership.student_card = student_card
            membership.save()

        messages.success(request, "Membership request submitted. Wait for librarian approval.")
        return redirect("lib:student_dashboard")

    # GET: show current membership state (none / pending / expired / rejected)
    return render(request, "lib/membership.html", {"membership": membership})

@login_required
def borrow_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    membership = Membership.objects.filter(user=request.user, status='active').first()
    if not membership:
        messages.error(request, 'You must be a member to borrow books.')
        return redirect('lib:membership')

    today = timezone.now().date()
    if membership.end_date < today:
        membership.status = 'expired'
        membership.save()
        messages.error(request, 'Your membership has expired. Please renew to borrow books.')
        return redirect('lib:membership')

    active_count = BorrowRequest.objects.filter(
        user=request.user,
        status__in=['pending', 'approved']
    ).count()
    if active_count >= membership.borrow_limit:
        messages.error(
            request,
            f'You reached your borrow limit of {membership.borrow_limit} books for this membership.'
        )
        return redirect('lib:student_dashboard')

    if book.stock < 1 or not book.available:
        messages.error(request, 'Book not available for borrowing.')
        return redirect('lib:book_detail', slug=book.slug)

    already_active = BorrowRequest.objects.filter(
        user=request.user,
        book=book,
        status__in=['pending', 'approved']
    ).exists()
    if already_active:
        messages.error(request, 'You already have a pending or approved request for this book.')
        return redirect('lib:student_dashboard')

    BorrowRequest.objects.create(user=request.user, book=book, status='pending')
    messages.success(request, 'Borrow request submitted.')
    return redirect('lib:student_dashboard')

@login_required
def student_dashboard(request):
    user = request.user
    if request.user.is_staff:
        return redirect('lib:librarian_dashboard')

    borrow_requests = BorrowRequest.objects.filter(user=request.user).order_by('-request_date')
    recommendations = recommend_for_user(user)
    membership = Membership.objects.filter(user=request.user).first()

    total_requests = borrow_requests.count()
    pending_count = borrow_requests.filter(status='pending').count()
    approved_count = borrow_requests.filter(status='approved').count()
    declined_count = borrow_requests.filter(status='declined').count()

    return render(request, 'lib/student_dashboard.html', {
        'borrow_requests': borrow_requests,
        'membership': membership,
        'total_requests': total_requests,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'declined_count': declined_count,
        'recommendations': recommendations,
    })




@login_required
def librarian_dashboard(request):
    if not request.user.is_staff:
        return redirect('lib:home')

    # Pending borrow requests
    borrow_requests = BorrowRequest.objects.filter(status='pending').order_by('request_date')

    all_reqs = BorrowRequest.objects.all()
    total_requests = all_reqs.count()
    pending_count = all_reqs.filter(status='pending').count()
    approved_count = all_reqs.filter(status='approved').count()
    declined_count = all_reqs.filter(status='declined').count()

    # NEW: pending membership requests
    pending_memberships = (
        Membership.objects
        .filter(status='pending')
        .select_related('user')
        .order_by('start_date')
    )

    return render(request, 'lib/librarian_dashboard.html', {
        'borrow_requests': borrow_requests,
        'total_requests': total_requests,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'declined_count': declined_count,
        'pending_memberships': pending_memberships,  # for template section
    })  

@staff_member_required
def approve_membership(request, membership_id):
    membership = get_object_or_404(Membership, id=membership_id, status="pending")
    today = timezone.now().date()
    membership.status = "active"
    membership.start_date = today
    membership.end_date = today + timedelta(days=365)
    if membership.borrow_limit == 0:
        membership.borrow_limit = 40  # or any default you prefer
    membership.save()
    messages.success(request, f"Membership approved for {membership.user.username}.")
    return redirect('lib:librarian_dashboard')

@staff_member_required
def reject_membership(request, membership_id):
    membership = get_object_or_404(Membership, id=membership_id, status="pending")
    membership.status = "rejected"
    membership.save()
    messages.warning(request, f"Membership request rejected for {membership.user.username}.")
    return redirect('lib:librarian_dashboard')
@login_required
def approve_borrow(request, req_id):
    if not request.user.is_staff:
        return redirect('lib:home')
    borrow_req = get_object_or_404(BorrowRequest, id=req_id)
    book = borrow_req.book
    if book.stock > 0:
        borrow_req.status = 'approved'
        borrow_req.return_date = timezone.now() + timedelta(days=14) 
        book.stock -= 1
        if book.stock <= 0:
            book.available = False
        book.save()
        borrow_req.save()
        messages.success(request, "Borrow request approved.")
    else:
        messages.error(request, "Book not in stock.")
    return redirect('lib:librarian_dashboard')

@login_required
def decline_borrow(request, req_id):
    if not request.user.is_staff:
        return redirect('lib:home')
    borrow_req = get_object_or_404(BorrowRequest, id=req_id)
    borrow_req.status = 'declined'
    borrow_req.save()
    messages.success(request, "Borrow request declined.")
    return redirect('lib:librarian_dashboard')


@login_required
def cancel_borrow_request(request, req_id):
    borrow_req = get_object_or_404(BorrowRequest, id=req_id, user=request.user)

    if borrow_req.status != 'pending':
        messages.error(request, 'Only pending requests can be cancelled.')
        return redirect('lib:student_dashboard')

    if request.method == 'POST':
        borrow_req.delete()
        messages.success(request, 'Borrow request cancelled.')
        return redirect('lib:student_dashboard')

    return redirect('lib:student_dashboard')

from django.contrib.admin.views.decorators import staff_member_required
from decimal import Decimal

@staff_member_required
def process_return(request):
    if request.method == 'POST':
        form = ReturnForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            book = form.cleaned_data['book']
            status = form.cleaned_data['status']

           
            borrow_req = BorrowRequest.objects.filter(
                user=user, book=book, status='approved'
            ).order_by('-request_date').first()

            if not borrow_req:
                messages.error(request, 'No approved borrow request found for this user and book.')
                return redirect('lib:process_return')

          
            borrow_req.status = 'returned'
            borrow_req.return_date = timezone.now()
            borrow_req.save()

          
            book.stock += 1
            if book.stock > 0:
                book.available = True
            book.save()

         
            if status == 'delay':
                membership = Membership.objects.filter(user=user).first()
                if membership:
                    membership.fine_balance += Decimal('50.00')
                    membership.save()
                messages.warning(request, 'Return processed with delay. Fine of ৳50 added.')
            else:
                messages.success(request, 'Return processed in time.')

            return redirect('lib:librarian_dashboard')
    else:
        form = ReturnForm()

    return render(request, 'lib/return_form.html', {'form': form})

@staff_member_required
def user_history(request, user_id):
    student = get_object_or_404(User, id=user_id)
    history = BorrowRequest.objects.filter(user=student).order_by('-request_date')
    membership = Membership.objects.filter(user=student).first()

    total_requests = history.count()
    returned_count = history.filter(status='returned').count()
    in_time_count = history.filter(status='returned', return_status='in_time').count() \
        if hasattr(BorrowRequest, 'return_status') else 0  

    returned_pct = round((returned_count / total_requests) * 100) if total_requests else 0
    in_time_pct = round((in_time_count / returned_count) * 100) if returned_count else 0

    return render(request, 'lib/user_history.html', {
        'student': student,
        'history': history,
        'membership': membership,
        'total_requests': total_requests,
        'returned_count': returned_count,
        'in_time_count': in_time_count,
        'returned_pct': returned_pct,
        'in_time_pct': in_time_pct,
    })

@staff_member_required
def users_overview(request):
  
    users = (
        User.objects
        .annotate(
            total_borrows=Count('borrowrequest', distinct=True),
            pending_borrows=Count('borrowrequest', filter=Q(borrowrequest__status='pending'), distinct=True),
            approved_borrows=Count('borrowrequest', filter=Q(borrowrequest__status='approved'), distinct=True),
            returned_borrows=Count('borrowrequest', filter=Q(borrowrequest__status='returned'), distinct=True),
        )
        .order_by('username')
    )

    memberships = {m.user_id: m for m in Membership.objects.all()}
    for u in users:
        u.membership_obj = memberships.get(u.id)

    return render(request, 'lib/users_overview.html', {
        'users': users,
    })
    
    
@login_required
def my_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
       
        if 'profile_submit' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
            password_form = PasswordChangeForm(user=request.user) 

            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('lib:my_profile')

        elif 'password_submit' in request.POST:
            user_form = UserUpdateForm(instance=request.user)
            profile_form = ProfileUpdateForm(instance=profile)
            password_form = PasswordChangeForm(user=request.user, data=request.POST)

            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # keep user logged in
                messages.success(request, 'Password changed successfully.')
                return redirect('lib:my_profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)
        password_form = PasswordChangeForm(user=request.user)

    return render(request, 'lib/my_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
    })
    


@login_required
@require_POST
def chat_api(request):
    message = request.POST.get("message", "").strip().lower()

    if not message:
        return JsonResponse({"reply": "Please type something so I can help."})

    user = request.user

    # 1) Membership / borrow limit
    if "membership" in message or "borrow limit" in message:
        membership = Membership.objects.filter(user=user).first()
        if not membership:
            reply = (
                "You do not have a membership yet. Go to the Membership page to submit a request."
            )
        else:
            reply = (
                f"Your membership status is {membership.status}. "
                f"Borrow limit: {membership.borrow_limit} books. "
                f"Valid until {membership.end_date}."
            )
        return JsonResponse({"reply": reply})

    # 2) Fines
    if "fine" in message or "dues" in message:
        membership = Membership.objects.filter(user=user).first()
        if not membership or membership.fine_balance <= 0:
            reply = "You have no outstanding fines."
        else:
            reply = f"Your outstanding fine is ৳{membership.fine_balance}."
        return JsonResponse({"reply": reply})

    # 3) My current books
    if "my books" in message or "current borrows" in message:
        borrows = BorrowRequest.objects.filter(
            user=user, status="approved"
        ).select_related("book")
        if not borrows:
            reply = "You have no currently borrowed books."
        else:
            titles = ", ".join(br.book.title for br in borrows)
            reply = f"Your currently borrowed books are: {titles}."
        return JsonResponse({"reply": reply})

    # 4) Simple book search: "books about X" / "book on X"
    if "book about" in message or "books about" in message or "book on" in message:
        # naive keyword extraction
        keywords = (
            message.replace("books about", "")
                   .replace("book about", "")
                   .replace("book on", "")
                   .strip()
        )
        if not keywords:
            return JsonResponse({"reply": "Please specify a topic, e.g. 'books about algorithms'."})

        books = Book.objects.filter(
            title__icontains=keywords
        )[:5]

        if not books:
            reply = f"No books found related to '{keywords}'."
        else:
            reply = "Here are some books I found: " + ", ".join(b.title for b in books) + "."
        return JsonResponse({"reply": reply})

    # 5) Default fallback
    reply = (
        "I am your library assistant. You can ask questions like:\n"
        "- 'What is my membership status?'\n"
        "- 'Do I have any fines?'\n"
        "- 'What are my current books?'\n"
        "- 'Books about algorithms'\n"
    )
    return JsonResponse({"reply": reply})