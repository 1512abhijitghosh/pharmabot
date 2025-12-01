import re
from fuzzywuzzy import process
import database

class PharmaAgent:
    def __init__(self, shop_id):
        self.shop_id = shop_id
        database.init_db()

    def extract_medicine_name(self, text, candidates):
        """Find the best match for medicine name in text from candidates."""
        if not candidates:
            return None
        # Simple extraction: check if any candidate is in text (fuzzy)
        # For MVP, let's just assume the text *contains* the name.
        # We can use process.extractOne to find the best match from the DB candidates against the user text.
        # But if the user text is "Where is Crocin", matching "Where is Crocin" against ["Crocin", "Aspirin"] might work.
        best_match = process.extractOne(text, candidates)
        if best_match and best_match[1] > 60: # Threshold
            return best_match[0]
        return None

    def process_query(self, user_input):
        user_input = user_input.strip()
        lower_input = user_input.lower()

        # Intent: ADD / UPDATE
        # Patterns: "Add 10 Aspirin to Box A", "Put 5 Crocin in Shelf 1"
        add_pattern = re.search(r"(add|put|update)\s+(\d+)\s+(.+)\s+(to|in|at)\s+(.+)", lower_input, re.IGNORECASE)
        if add_pattern:
            qty = int(add_pattern.group(2))
            med_raw = add_pattern.group(3).strip()
            loc_raw = add_pattern.group(5).strip()
            
            # Capitalize for DB consistency (optional)
            med_name = med_raw.title()
            loc_name = loc_raw.title()
            
            result = database.update_stock(self.shop_id, med_name, loc_name, qty)
            return f"✅ {result}"

        # Intent: SEARCH
        # Patterns: "Where is X", "Find X", "Search X"
        search_pattern = re.search(r"(where is|find|search|locate)\s+(.+)", lower_input, re.IGNORECASE)
        if search_pattern:
            med_raw = search_pattern.group(2).strip()
            # Remove question marks
            med_raw = med_raw.replace("?", "")
            
            # Try to find in DB
            results = database.find_medicine(self.shop_id, med_raw)
            
            if results.empty:
                return f"❌ I couldn't find any medicine matching '{med_raw}'."
            
            response = f"🔍 **Found '{med_raw}':**\n\n"
            for index, row in results.iterrows():
                response += f"- **{row['medicine']}**: {row['quantity']} units at *{row['location']}*\n"
            return response

        # Fallback: List all
        if "list" in lower_input or "show all" in lower_input:
            df = database.get_all_inventory(self.shop_id)
            if df.empty:
                return "Inventory is empty."
            return df

        return "❓ I didn't understand that. Try 'Where is Crocin?' or 'Add 10 Aspirin to Box A'."
