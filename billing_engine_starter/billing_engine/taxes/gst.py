"""
GSTCalculator — Indian Goods & Services Tax.

The rule:
    - If customer_state == seller_state (or seller_state is "")  =>  intra-state
        -> charge CGST + SGST (split equally, e.g. 9% + 9% = 18%)
    - Else  =>  inter-state
        -> charge IGST (e.g. 18%)

Customers without a state code default to IGST (safe choice).
"""

from decimal import Decimal

from billing_engine.money import Money
from billing_engine.taxes.base import TaxCalculator, TaxContext, TaxBreakdown


class GSTCalculator(TaxCalculator):
    def __init__(self, cgst: Decimal, sgst: Decimal, igst: Decimal) -> None:
        if not isinstance(cgst, Decimal) or not isinstance(sgst, Decimal) or not isinstance(igst, Decimal):
            raise TypeError("GST rates must be Decimal")
        if cgst < 0 or cgst > 1 or sgst < 0 or sgst > 1 or igst < 0 or igst > 1:
            raise ValueError("GST rates must be between 0 and 1")
        if cgst + sgst != igst:
            raise ValueError("CGST + SGST must equal IGST")
        self.cgst = cgst
        self.sgst = sgst
        self.igst = igst

    def apply(self, taxable: Money, context: TaxContext) -> TaxBreakdown:
        intra_state = bool(context.customer_state) and context.customer_state == context.seller_state
        if intra_state:
            cgst_amount_unrounded = taxable * self.cgst
            sgst_amount_unrounded = taxable * self.sgst
            # Round total AFTER adding to preserve precision
            total = (cgst_amount_unrounded + sgst_amount_unrounded).rounded()
            components = [
                (f"CGST {int(self.cgst * 100)}%", cgst_amount_unrounded.rounded()),
                (f"SGST {int(self.sgst * 100)}%", sgst_amount_unrounded.rounded()),
            ]
            return TaxBreakdown(components=components, total=total)

        igst_amount = (taxable * self.igst).rounded()
        return TaxBreakdown(components=[(f"IGST {int(self.igst * 100)}%", igst_amount)], total=igst_amount)
