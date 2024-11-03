class SearchableCardListMixin:
    def child_item_qs(self):
        raise NotImplementedError("This method must be implemented in the subclass.")
