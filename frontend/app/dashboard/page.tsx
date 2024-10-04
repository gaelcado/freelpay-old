// app/dashboard/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Invoice = {
  id: string
  created_date: string  // Changed from createdDate to match the backend
  amount: number
  client: string
  status: 'ongoing' | 'paid' | 'archived'
  financing_date?: string
  possible_financing?: number
  invoice_number: string
  due_date: string
  description?: string
  score?: number
}

export default function Dashboard() {
  const [invoices, setInvoices] = useState<Invoice[]>([])

  useEffect(() => {
    fetchInvoices()
  }, [])

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

  const handleAccept = async (id: string) => {
    try {
      const token = localStorage.getItem('token')
      await axios.post(`${API_URL}/invoices/${id}/accept`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      fetchInvoices()
    } catch (error) {
      console.error('Error accepting financing:', error)
    }
  }

  const handleRefuse = async (id: string) => {
    try {
      const token = localStorage.getItem('token')
      await axios.post(`${API_URL}/invoices/${id}/refuse`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      fetchInvoices()
    } catch (error) {
      console.error('Error refusing financing:', error)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-3xl font-bold">My Dashboard</CardTitle>
      </CardHeader>
      <CardContent>
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
            {invoices.map((invoice) => (
              <TableRow key={invoice.id}>
                <TableCell>{new Date(invoice.created_date).toLocaleString()}</TableCell>
                <TableCell>{invoice.amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</TableCell>
                <TableCell>{invoice.client}</TableCell>
                <TableCell>
                  <Badge variant={invoice.status === 'paid' ? 'default' : invoice.status === 'ongoing' ? 'secondary' : 'outline'}>
                    {invoice.status}
                  </Badge>
                </TableCell>
                <TableCell>{invoice.financing_date ? new Date(invoice.financing_date).toLocaleDateString() : '-'}</TableCell>
                <TableCell>{invoice.possible_financing ? `${invoice.possible_financing.toFixed(2)}%` : '-'}</TableCell>
                <TableCell>
                  {invoice.possible_financing && invoice.status === 'ongoing' && (
                    <div className="space-x-2">
                      <Button size="sm" onClick={() => handleAccept(invoice.id)}>Accept</Button>
                      <Button size="sm" variant="outline" onClick={() => handleRefuse(invoice.id)}>Refuse</Button>
                    </div>
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