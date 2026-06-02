# lib/recommender.py
from collections import Counter
from django.db.models import Count, Q
from .models import Book, BorrowRequest

MAX_RECS_PER_USER = 5

def get_user_history(user):
    return (
        BorrowRequest.objects
        .filter(user=user, status='returned')
        .values_list('book_id', flat=True)
        .distinct()
    )

def content_similar_books(book, limit=10):
    qs = Book.objects.filter(
        Q(category=book.category) | Q(author=book.author)
    ).exclude(id=book.id).annotate(
        borrow_count=Count('borrowrequest')
    ).order_by('-borrow_count')[:limit]
    return list(qs)

def cooccurrence_books(user_books_ids, limit=20):
    if not user_books_ids:
        return []

    co_borrows = (
        BorrowRequest.objects
        .filter(book_id__in=user_books_ids)
        .values('user_id')
        .annotate(c=Count('id'))
        .filter(c__gte=1)
    )
    user_ids = [row['user_id'] for row in co_borrows]

    others_books = (
        BorrowRequest.objects
        .filter(user_id__in=user_ids)
        .exclude(book_id__in=user_books_ids)
        .values_list('book_id', flat=True)
    )

    counts = Counter(others_books)
    top_ids = [book_id for book_id, _ in counts.most_common(limit)]
    books = Book.objects.filter(id__in=top_ids)
    # Preserve some order by borrow frequency
    return sorted(books, key=lambda b: counts[b.id], reverse=True)

def recommend_for_user(user, max_results=MAX_RECS_PER_USER):
    user_books_ids = list(get_user_history(user))

    # cold start: no history => popular books
    if not user_books_ids:
        popular = (
            Book.objects
            .annotate(borrow_count=Count('borrowrequest'))
            .order_by('-borrow_count')[:max_results]
        )
        return list(popular)

    # collaborative part
    collab_books = cooccurrence_books(user_books_ids, limit=max_results * 2)

    # content-based part: top N books user has read, get neighbors
    content_candidates = []
    for book in Book.objects.filter(id__in=user_books_ids)[:5]:
        content_candidates.extend(content_similar_books(book, limit=5))

    # merge, dedupe, drop already-read
    seen = set(user_books_ids)
    result = []
    for b in collab_books + content_candidates:
        if b.id in seen:
            continue
        if b in result:
            continue
        result.append(b)
        if len(result) >= max_results:
            break

    return result
