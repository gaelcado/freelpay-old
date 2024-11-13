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
import api from '@/lib/api'
import Confetti from 'react-confetti'
import { useRouter } from 'next/navigation'
import { useTranslation } from '@/hooks/useTranslation'
import { AxiosError } from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://freelpay.com/api";
console.log('API_URL', API_URL)

interface CreatedInvoice {
  id: string;
  invoice_number: string;
  client: string;
  client_email?: string;
  client_phone?: string;
  client_address?: string;
  client_postal_code?: string;
  client_city?: string;
  client_country?: string;
  client_vat_number?: string;
  client_type?: string;
  amount: number;
  currency?: string;
  due_date: string;
  description: string;
  payment_conditions?: string;
  language?: string;
  special_mentions?: string;
  possible_financing: number;
  status: string;
  created_date: string;
  score: number;
}

export default function NewInvoice() {
  const [invoiceNumber, setInvoiceNumber] = useState('')
  const [clientName, setClientName] = useState('')
  const [clientEmail, setClientEmail] = useState('')
  const [clientPhone, setClientPhone] = useState('')
  const [clientAddress, setClientAddress] = useState('')
  const [clientPostalCode, setClientPostalCode] = useState('')
  const [clientCity, setClientCity] = useState('')
  const [clientCountry, setClientCountry] = useState('FR')
  const [clientVatNumber, setClientVatNumber] = useState('')
  const [clientType, setClientType] = useState('company')
  const [amount, setAmount] = useState('')
  const [currency, setCurrency] = useState('EUR')
  const [dueDate, setDueDate] = useState('')
  const [description, setDescription] = useState('')
  const [paymentConditions, setPaymentConditions] = useState('upon_receipt')
  const [language, setLanguage] = useState('fr_FR')
  const [specialMentions, setSpecialMentions] = useState('')
  const [createdInvoice, setCreatedInvoice] = useState<CreatedInvoice | null>(null)
  const [isScoring, setIsScoring] = useState(false)
  const [showScoreDialog, setShowScoreDialog] = useState(false)
  const [showConfetti, setShowConfetti] = useState(false)
  const [score, setScore] = useState<number | null>(null); // Add this line
  const { toast } = useToast()
  const router = useRouter()
  const { t } = useTranslation()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const invoiceData = {
        invoice_number: invoiceNumber,
        client: clientName,
        client_email: clientEmail,
        client_phone: clientPhone,
        client_address: clientAddress,
        client_postal_code: clientPostalCode,
        client_city: clientCity,
        client_country: clientCountry,
        client_vat_number: clientVatNumber,
        client_type: clientType,
        amount: parseFloat(amount),
        currency: currency,
        due_date: dueDate,
        description: description,
        payment_conditions: paymentConditions,
        language: language,
        special_mentions: specialMentions,
        pdf_invoice_subject: `Devis ${invoiceNumber}`,
        pdf_invoice_free_text: specialMentions
      }

      const response = await api.post('/invoices/create', invoiceData)
      setCreatedInvoice(response.data)
      toast({
        title: t('createInvoice.successTitle'),
        description: t('createInvoice.successDescription'),
      })
    } catch (error) {
      console.error('Error creating invoice:', error)
      const errorMessage = error instanceof AxiosError 
        ? error.response?.data?.message || error.message 
        : t('createInvoice.errorDescription')
      
      toast({
        title: t('common.error'),
        description: errorMessage,
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
        const response = await api.post('/invoices/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        setCreatedInvoice(response.data)
        toast({
          title: t('createInvoice.uploadSuccessTitle'),
          description: t('createInvoice.uploadSuccessDescription'),
        })
      } catch (error) {
        console.error('Error uploading invoice:', error)
        const errorMessage = error instanceof AxiosError 
          ? error.response?.data?.detail || error.message 
          : t('createInvoice.uploadErrorDescription')
        
        toast({
          title: t('common.error'),
          description: errorMessage,
          variant: 'destructive',
        })
      }
    }
  }

  const handleScoreInvoice = async () => {
    if (!createdInvoice) return;

    setIsScoring(true);
    try {
      await api.post(`/invoices/${createdInvoice.id}/create-pennylane-estimate`);
      setScore(createdInvoice.score);
      setShowScoreDialog(true);
      setShowConfetti(true);
    } catch (error) {
      console.error('Error creating Pennylane estimate:', error);
      const errorMessage = error instanceof AxiosError 
        ? error.response?.data?.detail || error.message 
        : t('createInvoice.pennylaneError');
      
      toast({
        title: t('common.error'),
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsScoring(false);
    }
  };

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-3xl font-bold">{t('createInvoice.title')}</CardTitle>
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
                <div>
                  <Label htmlFor="invoiceNumber">{t('createInvoice.invoiceNumber')}</Label>
                  <Input
                    id="invoiceNumber"
                    value={invoiceNumber}
                    onChange={(e) => setInvoiceNumber(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="clientName">{t('createInvoice.clientName')}</Label>
                  <Input
                    id="clientName"
                    value={clientName}
                    onChange={(e) => setClientName(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="clientEmail">{t('createInvoice.clientEmail')}</Label>
                  <Input
                    id="clientEmail"
                    type="email"
                    value={clientEmail}
                    onChange={(e) => setClientEmail(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="clientPhone">{t('createInvoice.clientPhone')}</Label>
                  <Input
                    id="clientPhone"
                    value={clientPhone}
                    onChange={(e) => setClientPhone(e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="clientAddress">{t('createInvoice.clientAddress')}</Label>
                <Input
                  id="clientAddress"
                  value={clientAddress}
                  onChange={(e) => setClientAddress(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="clientPostalCode">{t('createInvoice.clientPostalCode')}</Label>
                  <Input
                    id="clientPostalCode"
                    value={clientPostalCode}
                    onChange={(e) => setClientPostalCode(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="clientCity">{t('createInvoice.clientCity')}</Label>
                  <Input
                    id="clientCity"
                    value={clientCity}
                    onChange={(e) => setClientCity(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="clientType">{t('createInvoice.clientType')}</Label>
                  <select
                    id="clientType"
                    value={clientType}
                    onChange={(e) => setClientType(e.target.value)}
                    className="w-full rounded-md border border-input px-3 py-2"
                  >
                    <option value="company">{t('createInvoice.companyType')}</option>
                    <option value="individual">{t('createInvoice.individualType')}</option>
                  </select>
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
              <div>
                <Label htmlFor="paymentConditions">{t('createInvoice.paymentConditions')}</Label>
                <select
                  id="paymentConditions"
                  value={paymentConditions}
                  onChange={(e) => setPaymentConditions(e.target.value)}
                  className="w-full rounded-md border border-input px-3 py-2"
                >
                  <option value="upon_receipt">{t('createInvoice.paymentUponReceipt')}</option>
                  <option value="30_days">{t('createInvoice.payment30Days')}</option>
                  <option value="60_days">{t('createInvoice.payment60Days')}</option>
                </select>
              </div>
              <div>
                <Label htmlFor="specialMentions">{t('createInvoice.specialMentions')}</Label>
                <Textarea
                  id="specialMentions"
                  value={specialMentions}
                  onChange={(e) => setSpecialMentions(e.target.value)}
                  className="h-20"
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
          <div className="mt-8">
            <h3 className="text-lg font-semibold mb-4">{t('createInvoice.createdInvoice')}</h3>
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
              {isScoring ? t('createInvoice.scoring') : t('createInvoice.scoreMyQuote')}
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
            <p>Your quote has a score of <strong>{createdInvoice?.score?.toFixed(2) ?? 'N/A'}</strong></p>
            <p className="mt-2">We are able to pay you an amount of <strong>${createdInvoice?.possible_financing?.toFixed(2) ?? 'N/A'}</strong> for this quote.</p>
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