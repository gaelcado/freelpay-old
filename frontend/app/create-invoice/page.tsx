// app/create-invoice/page.tsx
'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/components/ui/use-toast"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import { useTranslation } from '@/hooks/useTranslation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://freelpay.com/api";

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

export default function CreateInvoice() {
  const [invoiceNumber, setInvoiceNumber] = useState('')
  const [clientName, setClientName] = useState('')
  const [amount, setAmount] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [description, setDescription] = useState('')
  const [createdInvoice, setCreatedInvoice] = useState<CreatedInvoice | null>(null)
  const [isScoring, setIsScoring] = useState(false)
  const [showScoreDialog, setShowScoreDialog] = useState(false)
  const { toast } = useToast()
  const router = useRouter()
  const { t } = useTranslation()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await axios.post(`${API_URL}/invoices/create-demo`, {
        invoice_number: invoiceNumber,
        client: clientName,
        amount: parseFloat(amount),
        due_date: dueDate,
        description
      })
      setCreatedInvoice(response.data)
      toast({
        title: t('createInvoice.successTitle'),
        description: t('createInvoice.successDescription'),
      })
    } catch (error) {
      console.error('Error creating invoice:', error)
      toast({
        title: t('common.error'),
        description: t('createInvoice.errorDescription'),
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
        const response = await axios.post(`${API_URL}/invoices/upload-demo`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        setCreatedInvoice(response.data)
        toast({
          title: t('createInvoice.uploadSuccessTitle'),
          description: t('createInvoice.uploadSuccessDescription'),
        })
      } catch (error: any) {
        console.error('Error uploading invoice:', error)
        const errorMessage = error.response?.data?.detail || error.message || t('createInvoice.uploadErrorDescription')
        toast({
          title: t('common.error'),
          description: errorMessage,
          variant: 'destructive',
        })
      }
    }
  }

  const handleScoreInvoice = () => {
    if (!createdInvoice) return;
    setIsScoring(true);
    setTimeout(() => {
      setIsScoring(false);
      setShowScoreDialog(true);
    }, 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="text-3xl font-bold">{t('createInvoice.title')}</CardTitle>
          <CardDescription>{t('createInvoice.description')}</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="manual">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="manual">{t('createInvoice.createManually')}</TabsTrigger>
              <TabsTrigger value="upload">{t('createInvoice.uploadInvoice')}</TabsTrigger>
            </TabsList>
            <TabsContent value="manual">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="invoice-number">{t('createInvoice.invoiceNumber')}</Label>
                    <Input
                      id="invoice-number"
                      value={invoiceNumber}
                      onChange={(e) => setInvoiceNumber(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="client-name">{t('createInvoice.clientName')}</Label>
                    <Input
                      id="client-name"
                      value={clientName}
                      onChange={(e) => setClientName(e.target.value)}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="amount">{t('createInvoice.amount')}</Label>
                    <Input
                      id="amount"
                      type="number"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="due-date">{t('createInvoice.dueDate')}</Label>
                    <Input
                      id="due-date"
                      type="date"
                      value={dueDate}
                      onChange={(e) => setDueDate(e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">{t('createInvoice.description')}</Label>
                  <Textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>
                <Button type="submit" className="w-full">{t('createInvoice.createButton')}</Button>
              </form>
            </TabsContent>
            <TabsContent value="upload">
              <div className="space-y-4">
                <Label htmlFor="invoice-upload">{t('createInvoice.uploadInvoice')}</Label>
                <Input
                  id="invoice-upload"
                  type="file"
                  onChange={handleFileUpload}
                />
                <p className="text-sm text-muted-foreground">
                  {t('createInvoice.uploadDescription')}
                </p>
              </div>
            </TabsContent>
          </Tabs>
          {createdInvoice && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="mt-8"
            >
              <h3 className="text-lg font-semibold mb-4">{t('createInvoice.createdInvoice')}</h3>
              <div className="space-y-2">
                <p><strong>{t('createInvoice.invoiceNumber')}:</strong> {createdInvoice.invoice_number}</p>
                <p><strong>{t('createInvoice.clientName')}:</strong> {createdInvoice.client}</p>
                <p><strong>{t('createInvoice.amount')}:</strong> ${createdInvoice.amount.toFixed(2)}</p>
                <p><strong>{t('createInvoice.dueDate')}:</strong> {new Date(createdInvoice.due_date).toLocaleDateString()}</p>
                <p><strong>{t('createInvoice.description')}:</strong> {createdInvoice.description}</p>
                <p><strong>{t('invoice.status')}:</strong> {createdInvoice.status}</p>
                <p><strong>{t('dashboard.createdDate')}:</strong> {new Date(createdInvoice.created_date).toLocaleDateString()}</p>
              </div>
              <Button 
                onClick={handleScoreInvoice} 
                className="mt-4 w-full"
                disabled={isScoring}
              >
                {isScoring ? t('createInvoice.scoring') : t('createInvoice.scoreButton')}
              </Button>
            </motion.div>
          )}
        </CardContent>
      </Card>
      <Dialog open={showScoreDialog} onOpenChange={setShowScoreDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('createInvoice.scoreTitle')}</DialogTitle>
            <DialogDescription>
              {t('createInvoice.scoreDescription')}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-2xl font-bold text-center">
              {t('createInvoice.score')}: {createdInvoice?.score.toFixed(2)}
            </p>
            <p className="mt-4">
              {t('createInvoice.financingOffer')}<strong>${createdInvoice?.possible_financing.toFixed(2)}</strong> for this invoice.
            </p>
          </div>
          <DialogFooter>
            <Button onClick={() => router.push('/')} variant="outline">
              {t('createInvoice.maybeLater')}
            </Button>
            <Button onClick={() => router.push('/')}>
              {t('createInvoice.createAccount')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}