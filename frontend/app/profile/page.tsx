// app/profile/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useToast } from "@/components/ui/use-toast"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import api from '@/lib/api'
import { useAuth } from '@/components/AuthContext' // Import the Auth context
import { useTranslation } from '@/hooks/useTranslation' // Ajouter le hook de traduction

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://freelpay.com'
console.log('API_URL', API_URL)

interface OriginalData {
  email: string;
  siret_number: string;
  phone: string;
  address: string;
  id_document?: string; 
  id_document_status?: string; 
}

export default function Profile() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [siret, setSiret] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [hasChanges, setHasChanges] = useState(false)
  const [originalData, setOriginalData] = useState<OriginalData>({
    email: '',
    siret_number: '',
    phone: '',
    address: '',
    id_document: undefined,
    id_document_status: 'not_uploaded' // Initialize with default status
  });
  const [idDocument, setIdDocument] = useState<string | null>(null); // State for ID document
  const [idDocumentStatus, setIdDocumentStatus] = useState('not_uploaded'); // State for ID document status
  const { toast } = useToast()
  const { t } = useTranslation() // Ajouter le hook de traduction

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const response = await api.get('/users/me')
      const userData = response.data

      // Populate fields based on user data
      setName(userData.username || ''); // Set name if available
      setEmail(userData.email || ''); // Always set email
      setSiret(userData.siret_number || ''); // Set SIRET if available
      setPhone(userData.phone || ''); // Set phone if available
      setAddress(userData.address || ''); // Set address if available
      setIdDocument(userData.id_document || null);
      setIdDocumentStatus(userData.id_document_status || 'not_uploaded'); // Set ID document status

      setOriginalData({
        email: userData.email,
        siret_number: userData.siret_number || '',
        phone: userData.phone || '',
        address: userData.address || '',
        id_document: userData.id_document || null,
        id_document_status: userData.id_document_status || 'not_uploaded'
      });
    } catch (error) {
      console.error('Error fetching user profile:', error);
    }
  };

  const handleInputChange = (setter: React.Dispatch<React.SetStateAction<string>>, value: string) => {
    setter(value)
    checkForChanges()
  }

  const checkForChanges = () => {
    const originalDataTyped = originalData as OriginalData;
    const hasChanged = 
      email !== originalDataTyped.email ||
      siret !== originalDataTyped.siret_number ||
      phone !== originalDataTyped.phone ||
      address !== originalDataTyped.address ||
      idDocument !== originalDataTyped.id_document; // Check for changes in id_document
    setHasChanges(hasChanged);
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.put('/users/update', {
        email,
        siret_number: siret,
        phone,
        address
      })
      toast({
        title: t('common.success'),
        description: t('profile.updateSuccess'),
      })
      setHasChanges(false)
      setOriginalData({ email, siret_number: siret, phone, address })
    } catch (error) {
      console.error('Error updating profile:', error)
      toast({
        title: t('common.error'),
        description: t('profile.updateError'),
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
        await api.post('/users/upload-id', formData, {
          headers: { 
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${token}`
          }
        })
        toast({
          title: t('common.success'),
          description: t('profile.updateSuccess'),
        })
        setIdDocument(URL.createObjectURL(file))
      } catch (error) {
        console.error('Error uploading ID document:', error)
        toast({
          title: t('common.error'),
          description: t('profile.updateError'),
          variant: 'destructive',
        })
      }
    }
  }

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-3xl font-bold">{t('profile.title')}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">{t('common.username')}</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">{t('common.email')}</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => handleInputChange(setEmail, e.target.value)}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="siret">{t('common.siretNumber')}</Label>
              <Input
                id="siret"
                value={siret}
                onChange={(e) => handleInputChange(setSiret, e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">{t('common.phone')}</Label>
              <Input
                id="phone"
                type="tel"
                value={phone}
                onChange={(e) => handleInputChange(setPhone, e.target.value)}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="address">{t('common.address')}</Label>
            <Input
              id="address"
              value={address}
              onChange={(e) => handleInputChange(setAddress, e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="id-document">{t('profile.idDocument')}</Label>
            {idDocument ? (
              <div>
                {idDocument.endsWith('.pdf') ? (
                  <a href={idDocument} target="_blank" rel="noopener noreferrer">
                    {t('profile.viewIdDocument')}
                  </a>
                ) : (
                  <img src={idDocument} alt={t('profile.idDocumentPreview')} className="w-full h-auto" />
                )}
              </div>
            ) : (
              <Input
                id="id-document"
                type="file"
                onChange={handleFileUpload}
                disabled={idDocumentStatus === 'verified' || idDocumentStatus === 'pending'}
              />
            )}
          </div>
          <div className="flex items-center space-x-2">
            <span>{t('profile.verificationStatus')}:</span>
            <Badge variant={
              idDocumentStatus === 'verified' ? "default" : 
              idDocumentStatus === 'pending' ? "secondary" : 
              idDocumentStatus === 'rejected' ? "destructive" : 
              undefined
            }>
              {idDocumentStatus === 'verified' ? t('profile.verified') : 
               idDocumentStatus === 'pending' ? t('profile.pendingValidation') : 
               t('profile.notVerified')}
            </Badge>
          </div>
          <Button type="submit" className="w-full" disabled={!hasChanges}>
            {t('profile.updateProfile')}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}