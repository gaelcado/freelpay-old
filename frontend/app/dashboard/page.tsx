'use client'

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import api from '@/lib/api'
import { format } from 'date-fns'
import { DateRangePicker } from '@/components/ui/react-day-picker'
import { DateRange } from 'react-day-picker'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { useTranslation } from '@/hooks/useTranslation'
import { useToast } from "@/components/ui/use-toast"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://freelpay.com/api";
console.log('API_URL', API_URL)

type Invoice = {
  id: string
  created_date: string
  amount: number
  client: string
  status: 'Sent' | 'Signed' | 'Freelpaid' | 'Draft'
  financing_date?: string
  possible_financing?: number
  invoice_number: string
  due_date: string
  description?: string
  score?: number
}

export default function Dashboard() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [filteredInvoices, setFilteredInvoices] = useState<Invoice[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [dateRange, setDateRange] = useState<DateRange | undefined>()
  const [showSendDialog, setShowSendDialog] = useState(false) // State for dialog visibility
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null) // State to hold the selected invoice ID
  const { t } = useTranslation()
  const { toast } = useToast()

  useEffect(() => {
    fetchInvoices()
  }, [])

  useEffect(() => {
    filterInvoices()
  }, [invoices, searchTerm, statusFilter, dateRange])

  const fetchInvoices = async () => {
    try {
      const response = await api.get('/invoices/list')
      setInvoices(response.data)
    } catch (error) {
      console.error('Error fetching invoices:', error)
    }
  }

  const filterInvoices = () => {
    let filtered = invoices

    if (searchTerm) {
      filtered = filtered.filter(invoice => 
        invoice.client.toLowerCase().includes(searchTerm.toLowerCase()) ||
        invoice.invoice_number.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    if (statusFilter && statusFilter !== 'all') {
      filtered = filtered.filter(invoice => invoice.status === statusFilter)
    }

    if (dateRange && dateRange.from && dateRange.to) { // Added check for dateRange
      filtered = filtered.filter(invoice => {
        if (!dateRange.from || !dateRange.to) return false; // Ensure from and to are defined
        const invoiceDate = new Date(invoice.created_date)
        return invoiceDate >= dateRange.from && invoiceDate <= dateRange.to
      })
    }

    setFilteredInvoices(filtered)
  }

  const handleSend = (invoiceId: string) => {
    setSelectedInvoiceId(invoiceId); // Set the selected invoice ID
    setShowSendDialog(true); // Show the confirmation dialog
  };

  const confirmSendInvoice = async () => {
    if (selectedInvoiceId) {
      try {
        await api.post(`/invoices/${selectedInvoiceId}/send`)
        await fetchInvoices() // Rafraîchir la liste des factures
        toast({
          title: t('dashboard.sendSuccess'),
          description: t('dashboard.invoiceSentSuccessfully'),
        })
      } catch (error) {
        console.error('Error sending invoice:', error)
        toast({
          title: t('common.error'),
          description: t('dashboard.errorSendingInvoice'),
          variant: 'destructive',
        })
      }
      setShowSendDialog(false)
    }
  }

  const handleView = (invoiceId: string) => {
    console.log('Viewing invoice:', invoiceId)
  }

  const getStatusColor = (status: string | null) => {
    switch (status) {
      case 'Sent': return 'bg-blue-500 hover:bg-blue-600'
      case 'Signed': return 'bg-green-500 hover:bg-green-600'
      case 'Freelpaid': return 'bg-purple-500 hover:bg-purple-600'
      default: return 'bg-gray-500 hover:bg-gray-600'
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-3xl font-bold">{t('dashboard.title')}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="flex-1">
            <Label htmlFor="search">{t('dashboard.search')}</Label>
            <Input
              id="search"
              placeholder={t('common.searchPlaceholder')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="w-full md:w-48">
            <Label htmlFor="status">{t('dashboard.status')}</Label>
            <Select onValueChange={setStatusFilter}>
              <SelectTrigger id="status">
                <SelectValue placeholder={t('common.all')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('common.all')}</SelectItem>
                <SelectItem value="Sent">Sent</SelectItem>
                <SelectItem value="Signed">Signed</SelectItem>
                <SelectItem value="Freelpaid">Freelpaid</SelectItem>
                <SelectItem value="Ongoing">Ongoing</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="w-full md:w-auto">
            <Label>{t('dashboard.dateRange')}</Label>
            <DateRangePicker onChange={setDateRange} />
          </div>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t('dashboard.createdDate')}</TableHead>
              <TableHead>{t('dashboard.amount')}</TableHead>
              <TableHead>{t('dashboard.client')}</TableHead>
              <TableHead>{t('dashboard.status')}</TableHead>
              <TableHead>{t('dashboard.financingDate')}</TableHead>
              <TableHead>{t('dashboard.possibleFinancing')}</TableHead>
              <TableHead>{t('dashboard.actions')}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredInvoices.map((invoice) => (
              <TableRow key={invoice.id}>
                <TableCell>{format(new Date(invoice.created_date), 'PP')}</TableCell>
                <TableCell>{invoice.amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</TableCell>
                <TableCell>{invoice.client}</TableCell>
                <TableCell>
                  <Badge className={`${getStatusColor(invoice.status)} text-white`}>
                    {invoice.status || 'None'}
                  </Badge>
                </TableCell>
                <TableCell>{invoice.financing_date ? format(new Date(invoice.financing_date), 'PP') : '-'}</TableCell>
                <TableCell>
                  {invoice.possible_financing 
                    ? invoice.possible_financing.toLocaleString('en-US', { style: 'currency', currency: 'USD' }) 
                    : '-'}
                </TableCell>
                <TableCell>
                  {invoice.status === 'Draft' && (
                    <div className="space-x-2">
                      <Button size="sm" onClick={() => handleSend(invoice.id)}>{t('dashboard.send')}</Button>
                      <Button size="sm" variant="outline" onClick={() => handleView(invoice.id)}>{t('dashboard.view')}</Button>
                    </div>
                  )}
                  {(invoice.status === 'Sent' || invoice.status === 'Signed' || invoice.status === 'Freelpaid') && (
                    <Button size="sm" variant="outline" onClick={() => handleView(invoice.id)}>{t('dashboard.view')}</Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
      <Dialog open={showSendDialog} onOpenChange={setShowSendDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('dashboard.confirmSendTitle')}</DialogTitle>
          </DialogHeader>
          <div>
            {t('dashboard.confirmSendMessage')}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSendDialog(false)}>{t('dashboard.cancel')}</Button>
            <Button onClick={confirmSendInvoice}>{t('dashboard.send')}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}