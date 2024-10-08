// app/new-invoice/page.tsx
'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/components/ui/use-toast"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import axios from 'axios'
import Confetti from 'react-confetti'
import { useRouter } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://freelpay-nextjs-pm2fo.ondigitalocean.app/api'
console.log('API_URL', API_URL)

interface CreatedInvoice {
  id: string;
  invoice_number: string;
  client: string;
  amount: number;
  due_date: string;
  description: string;
  possible_financing: number;
  status: string;
  created_date: string;
  score: number;
}

export default function NewInvoice() {
  const [invoiceNumber, setInvoiceNumber] = useState('')
  const [clientName, setClientName] = useState('')
  const [amount, setAmount] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [description, setDescription] = useState('')
  const [createdInvoice, setCreatedInvoice] = useState<CreatedInvoice | null>(null)
  const [isScoring, setIsScoring] = useState(false)
  const [showScoreDialog, setShowScoreDialog] = useState(false)
  const [showConfetti, setShowConfetti] = useState(false)
  const [score, setScore] = useState<number | null>(null); // Add this line
  const { toast } = useToast()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(`${API_URL}/invoices/create`, {
        invoice_number: invoiceNumber,
        client: clientName,
        amount: parseFloat(amount),
        due_date: dueDate,
        description
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setCreatedInvoice(response.data)
      toast({
        title: 'Invoice Created',
        description: `Invoice created successfully. You can score it now.`,
      })
    } catch (error) {
      console.error('Error creating invoice:', error)
      toast({
        title: 'Error',
        description: 'Failed to create invoice. Please try again.',
        variant: 'destructive',
      })
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const formData = new FormData()
      formData.append('file', file)
      try {
        const token = localStorage.getItem('token')
        const response = await axios.post(`${API_URL}/invoices/upload`, formData, {
          headers: { 
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${token}`
          }
        })
        setCreatedInvoice(response.data)
        toast({
          title: 'Invoice Uploaded',
          description: 'Your invoice has been successfully uploaded and processed.',
        })
      } catch (error) {
        console.error('Error uploading invoice:', error)
        toast({
          title: 'Error',
          description: 'Failed to upload invoice. Please try again.',
          variant: 'destructive',
        })
      }
    }
  }

  const handleScoreInvoice = () => {
    if (!createdInvoice) return;

    // Directly use the score from the createdInvoice
    setScore(createdInvoice.score); // Set the score from the created invoice
    setShowScoreDialog(true); // Show the score dialog
    setShowConfetti(true); // Show confetti animation
  };

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-3xl font-bold">Create New Invoice</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="manual">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="manual">Create Manually</TabsTrigger>
            <TabsTrigger value="upload">Upload Invoice</TabsTrigger>
          </TabsList>
          <TabsContent value="manual">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="invoice-number">Invoice Number</Label>
                  <Input
                    id="invoice-number"
                    value={invoiceNumber}
                    onChange={(e) => setInvoiceNumber(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="client-name">Client Name</Label>
                  <Input
                    id="client-name"
                    value={clientName}
                    onChange={(e) => setClientName(e.target.value)}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="amount">Amount</Label>
                  <Input
                    id="amount"
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="due-date">Due Date</Label>
                  <Input
                    id="due-date"
                    type="date"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
              <Button type="submit" className="w-full">Create Invoice</Button>
            </form>
          </TabsContent>
          <TabsContent value="upload">
            <div className="space-y-4">
              <Label htmlFor="invoice-upload">Upload Invoice</Label>
              <Input
                id="invoice-upload"
                type="file"
                onChange={handleFileUpload}
              />
              <p className="text-sm text-muted-foreground">
                Upload your invoice file (PDF, JPG, PNG) and we'll process it for you.
              </p>
            </div>
          </TabsContent>
        </Tabs>
        {createdInvoice && (
          <div className="mt-8">
            <h3 className="text-lg font-semibold mb-4">Created Invoice</h3>
            <div className="space-y-2">
              <p><strong>Invoice Number:</strong> {createdInvoice.invoice_number}</p>
              <p><strong>Client:</strong> {createdInvoice.client}</p>
              <p><strong>Amount:</strong> ${createdInvoice.amount.toFixed(2)}</p>
              <p><strong>Due Date:</strong> {new Date(createdInvoice.due_date).toLocaleDateString()}</p>
              <p><strong>Description:</strong> {createdInvoice.description}</p>
              <p><strong>Status:</strong> {createdInvoice.status}</p>
              <p><strong>Created Date:</strong> {new Date(createdInvoice.created_date).toLocaleDateString()}</p>
            </div>
            <Button 
              onClick={handleScoreInvoice} 
              className="mt-4 w-full"
              disabled={isScoring}
            >
              {isScoring ? 'Scoring...' : 'Score my invoice'}
            </Button>
          </div>
        )}
      </CardContent>
      <Dialog open={showScoreDialog} onOpenChange={setShowScoreDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Congratulations!</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p>Your invoice has a score of <strong>{createdInvoice?.score?.toFixed(2) ?? 'N/A'}</strong></p>
            <p className="mt-2">We are able to pay you an amount of <strong>${createdInvoice?.possible_financing?.toFixed(2) ?? 'N/A'}</strong> for this invoice.</p>
          </div>
          <Button onClick={() => {
            setShowScoreDialog(false)
            setShowConfetti(false)
            router.push('/dashboard')
          }}>
            Go to Dashboard
          </Button>
        </DialogContent>
      </Dialog>
      {showConfetti && <Confetti />}
    </Card>
  )
}