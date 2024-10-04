'use client'

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import axios from 'axios'
import { format } from 'date-fns'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Invoice = {
  id: string
  created_date: string
  amount: number
  client: string
  status: 'sent' | 'accepted' | 'financed' | null
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
  const [dateRange, setDateRange] = useState<{ from: Date; to: Date } | undefined>()

  useEffect(() => {
    fetchInvoices()
  }, [])

  useEffect(() => {
    filterInvoices()
  }, [invoices, searchTerm, statusFilter, dateRange])

  const fetchInvoices = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_URL}/invoices`, {
        headers: { Authorization: `Bearer ${token}` }
      })
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

    if (statusFilter && statusFilter !== 'all') { // Check if statusFilter is not 'all'
      filtered = filtered.filter(invoice => invoice.status === statusFilter)
    }

    if (dateRange?.from && dateRange?.to) {
      filtered = filtered.filter(invoice => {
        const invoiceDate = new Date(invoice.created_date)
        return invoiceDate >= dateRange.from && invoiceDate <= dateRange.to
      })
    }

    setFilteredInvoices(filtered)
  }

  const handleSend = async (invoiceId: string) => {
    try {
      const token = localStorage.getItem('token')
      await axios.post(`${API_URL}/invoices/${invoiceId}/send`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      fetchInvoices()
    } catch (error) {
      console.error('Error sending invoice:', error)
    }
  }

  const handleView = (invoiceId: string) => {
    // Implement view functionality (e.g., open a modal with invoice details)
    console.log('Viewing invoice:', invoiceId)
  }

  const getStatusColor = (status: string | null) => {
    switch (status) {
      case 'sent': return 'bg-blue-500 hover:bg-blue-600'
      case 'accepted': return 'bg-green-500 hover:bg-green-600'
      case 'financed': return 'bg-purple-500 hover:bg-purple-600'
      default: return 'bg-gray-500 hover:bg-gray-600'
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-3xl font-bold">My Dashboard</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="flex-1">
            <Label htmlFor="search">Search</Label>
            <Input
              id="search"
              placeholder="Search by client or invoice number"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="w-full md:w-48">
            <Label htmlFor="status">Status</Label>
            <Select onValueChange={setStatusFilter}>
              <SelectTrigger id="status">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="sent">Sent</SelectItem>
                <SelectItem value="accepted">Accepted</SelectItem>
                <SelectItem value="financed">Financed</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="w-full md:w-auto">
            <Label>Date Range</Label>
          </div>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Created Date</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Client</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Financing Date</TableHead>
              <TableHead>Possible Financing</TableHead>
              <TableHead>Actions</TableHead>
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
                  {!invoice.status && (
                    <div className="space-x-2">
                      <Button size="sm" onClick={() => handleSend(invoice.id)}>Send</Button>
                      <Button size="sm" variant="outline" onClick={() => handleView(invoice.id)}>View</Button>
                    </div>
                  )}
                  {(invoice.status === 'sent' || invoice.status === 'accepted' || invoice.status === 'financed') && (
                    <Button size="sm" variant="outline" onClick={() => handleView(invoice.id)}>View</Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}