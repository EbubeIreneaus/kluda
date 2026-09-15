export const customerStatusColors: Record<string, string> = {
  active: 'success',
  inactive: 'neutral',
}

export const debtStatusColors: Record<string, string> = {
  unpaid: 'warning',
  overdue: 'error',
  paid: 'success',
}

export const statusOptions = [
  { label: 'Active', value: 'active' },
  { label: 'Inactive', value: 'inactive' },
]

export const debtStatusOptions = [
  { label: 'Unpaid', value: 'unpaid' },
  { label: 'Overdue', value: 'overdue' },
  { label: 'Paid', value: 'paid' },
]

export const customerTabs = [
  { label: 'Customers', value: 'customers', icon: 'i-lucide-users' },
  { label: 'Debts', value: 'debts', icon: 'i-lucide-banknote' },
]
