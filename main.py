import asyncio
from datetime import datetime, timedelta


BookStore = dict[int, dict[str, str]]
BorrowedStore = dict[int, dict[str, object]]
FineStore = dict[int, float]

library_inventory: BookStore = {
    101: {"title": "C++ for Beginner", "author": "A. John", "category": "Programming"},
    102: {"title": "Data Structures 101", "author": "M. Cole", "category": "Programming"},
    103: {"title": "English Grammar", "author": "R. Mary", "category": "Language"},
    104: {"title": "Math Basics", "author": "K. Paul", "category": "Education"},
}

borrowed_books: BorrowedStore = {}
user_fines: FineStore = {}
fine_per_day = 2.0
lock = asyncio.Lock()


async def search_books(title: str = "", author: str = "", category: str = "") -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []

    for book_id, info in library_inventory.items():
        if title and title.lower() not in info["title"].lower():
            continue
        if author and author.lower() not in info["author"].lower():
            continue
        if category and category.lower() not in info["category"].lower():
            continue
        matches.append({"book_id": book_id, "title": info["title"], "author": info["author"], "category": info["category"]})

    return matches


async def borrow_book(user_id: int, book_id: int, borrow_days: int = 7) -> str:
    print(f"User {user_id} is requesting book {book_id}...")
    await asyncio.sleep(1)

    async with lock:
        if book_id not in library_inventory:
            return f"ERROR: Book {book_id} is not available."

        book_info = library_inventory.pop(book_id)
        due_date = datetime.now() + timedelta(days=borrow_days)
        borrowed_books[book_id] = {
            "user_id": user_id,
            "title": book_info["title"],
            "author": book_info["author"],
            "category": book_info["category"],
            "borrowed_at": datetime.now(),
            "due_date": due_date,
        }
        return f"SUCCESS: User {user_id} borrowed '{book_info['title']}' and should return by {due_date.date()}."


async def return_book(user_id: int, book_id: int) -> str:
    print(f"User {user_id} is returning book {book_id}...")
    await asyncio.sleep(1)

    async with lock:
        if book_id not in borrowed_books:
            return f"ERROR: Book {book_id} was not borrowed."

        record = borrowed_books[book_id]
        if record["user_id"] != user_id:
            return f"ERROR: Book {book_id} was not borrowed by user {user_id}."

        due_date = record["due_date"]
        now_time = datetime.now()
        overdue_days = (now_time - due_date).days
        if overdue_days < 0:
            overdue_days = 0

        fine = overdue_days * fine_per_day
        if fine > 0:
            old_fine = user_fines.get(user_id, 0.0)
            user_fines[user_id] = old_fine + fine

        returned_info = {
            "title": record["title"],
            "author": record["author"],
            "category": record["category"],
        }
        library_inventory[book_id] = returned_info
        del borrowed_books[book_id]

        return f"SUCCESS: User {user_id} returned book {book_id}. Overdue days: {overdue_days}, Fine: {fine}"


async def show_overdue_books() -> None:
    print("\n--- OVERDUE BOOK REPORT ---")
    now_time = datetime.now()
    found = False

    for book_id, record in borrowed_books.items():
        overdue_days = (now_time - record["due_date"]).days
        if overdue_days > 0:
            found = True
            print(
                f"Book {book_id} ({record['title']}) is overdue by {overdue_days} days. "
                f"Current fine: {overdue_days * fine_per_day}"
            )

    if not found:
        print("No overdue books right now.")


async def show_user_fines(user_id: int) -> None:
    fine = user_fines.get(user_id, 0.0)
    print(f"User {user_id} total outstanding fine: {fine}")


async def main() -> None:
    print("--- Library Async Simulation Starting ---\n")

    print("1) Searching for Programming books")
    search_result = await search_books(category="Programming")
    for item in search_result:
        print(item)

    print("\n2) Borrowing books with multiple users at same time")
    task1 = borrow_book(1, 101, borrow_days=0)
    task2 = borrow_book(2, 102, borrow_days=3)
    task3 = borrow_book(3, 101, borrow_days=5)  # This should fail because 101 is already taken
    borrow_results = await asyncio.gather(task1, task2, task3)
    for res in borrow_results:
        print(res)

    print("\n3) Simulate overdue and return")
    # Force one book to become overdue for demo
    if 101 in borrowed_books:
        borrowed_books[101]["due_date"] = datetime.now() - timedelta(days=2)

    await show_overdue_books()

    return_result = await return_book(1, 101)
    print(return_result)

    await show_user_fines(1)

    print("\n4) Current inventory after returns")
    for book_id, info in library_inventory.items():
        print(book_id, info)


if __name__ == "__main__":
    asyncio.run(main())