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
import { useTranslation } from '@/hooks/useTranslation'
import { validateSiren, CompanyInfo } from '@/lib/sirenApi'
import { getStatusText, getStaffCategory } from '@/lib/utils/companyUtils'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://app.freelpay.com'
console.log('API_URL', API_URL)

interface OriginalData {
  email: string;
  siren_number: string;
  phone: string;
  address: string;
  id_document?: string; 
  id_document_status?: string; 
}

export default function Profile() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [siren, setSiren] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [hasChanges, setHasChanges] = useState(false)
  const [originalData, setOriginalData] = useState<OriginalData>({
    email: '',
    siren_number: '',
    phone: '',
    address: '',
    id_document: undefined,
    id_document_status: 'not_uploaded'
  });
  const [idDocument, setIdDocument] = useState<string | null>(null);
  const [idDocumentStatus, setIdDocumentStatus] = useState('not_uploaded');
  const [registrationMethod, setRegistrationMethod] = useState<'email' | 'google' | null>(null);
  const [sirenLocked, setSirenLocked] = useState(false);
  const { toast } = useToast()
  const { t } = useTranslation()
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo | null>(null);

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const response = await api.get('/users/me')
      const userData = response.data

      // Remplir les champs en fonction des données de l'utilisateur
      setName(userData.username || '');
      setEmail(userData.email || '');
      setSiren(userData.siren_number || '');
      setPhone(userData.phone || '');
      setAddress(userData.address || '');
      setIdDocument(userData.id_document || null);
      setIdDocumentStatus(userData.id_document_status || 'not_uploaded');

      // Déterminer la méthode d'inscription et si le SIREN est verrouillé
      setRegistrationMethod(userData.registration_method || 'email');
      setSirenLocked(userData.registration_method === 'email' || userData.siren_number);

      setOriginalData({
        email: userData.email,
        siren_number: userData.siren_number || '',
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
      siren !== originalDataTyped.siren_number ||
      phone !== originalDataTyped.phone ||
      address !== originalDataTyped.address ||
      idDocument !== originalDataTyped.id_document;
    setHasChanges(hasChanged);
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      // Si le SIREN a changé et n'est pas verrouillé, le valider d'abord
      if (siren !== originalData.siren_number && !sirenLocked) {
        try {
          await validateSiren(siren, t)
        } catch (error: any) {
          toast({
            title: t('common.error'),
            description: error.message,
            variant: 'destructive',
          })
          return
        }
      }

      await api.put('/users/update', {
        email,
        siren_number: siren,
        phone,
        address
      })
      toast({
        title: t('common.success'),
        description: t('profile.updateSuccess'),
      })
      setHasChanges(false)
      setOriginalData({ email, siren_number: siren, phone, address })
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

  const handleSirenValidation = async () => {
    if (siren.length !== 9) {
      toast({
        title: t('common.error'),
        description: t('common.sirenValidation.incorrectFormat'),
        variant: "destructive"
      });
      return;
    }

    try {
      const company = await validateSiren(siren, t);
      setCompanyInfo(company);
      setAddress(company.address);
      
      toast({
        title: t('common.sirenValidation.companyFound'),
        description: (
          <div className="mt-2 space-y-2">
            <p className="font-semibold text-lg">{company.name}</p>
            <p><strong>{t('common.sirenValidation.companyDetails.siren')} :</strong> {company.siren}</p>
            <p><strong>{t('common.sirenValidation.companyDetails.address')} :</strong> {company.address}</p>
            {company.activity && (
              <p><strong>{t('common.sirenValidation.companyDetails.mainActivity')} :</strong> {company.activity}</p>
            )}
            {company.creation_date && (
              <p><strong>{t('common.sirenValidation.companyDetails.creationDate')} :</strong> {new Date(company.creation_date).toLocaleDateString()}</p>
            )}
            {company.status && (
              <p><strong>{t('common.sirenValidation.companyDetails.status')} :</strong> {getStatusText(company.status, t)}</p>
            )}
            {company.staff_category && (
              <p><strong>{t('common.sirenValidation.companyDetails.staffing')} :</strong> {getStaffCategory(company.staff_category)}
                {company.staff_year && ` (${company.staff_year})`}
              </p>
            )}
            {company.company_category && (
              <p><strong>{t('common.sirenValidation.companyDetails.category')} :</strong> {company.company_category}</p>
            )}
            {company.social_economy && (
              <p><strong>{t('common.sirenValidation.companyDetails.socialEconomy')} :</strong> {company.social_economy === 'O' ? t('common.sirenValidation.companyDetails.yes') : t('common.sirenValidation.companyDetails.no')}</p>
            )}
            {company.employer && (
              <p><strong>{t('common.sirenValidation.companyDetails.employer')} :</strong> {company.employer === 'O' ? t('common.sirenValidation.companyDetails.yes') : t('common.sirenValidation.companyDetails.no')}</p>
            )}
          </div>
        ),
        duration: 10000,
      });
    } catch (error: any) {
      toast({
        title: t('common.error'),
        description: error.message,
        variant: "destructive"
      });
    }
    checkForChanges();
  };

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
              <Label htmlFor="siren">{t('common.sirenNumber')}</Label>
              <div className="flex gap-2">
                <Input
                  id="siren"
                  value={siren}
                  onChange={(e) => setSiren(e.target.value.replace(/[^0-9]/g, '').slice(0, 9))}
                  disabled={sirenLocked}
                  maxLength={9}
                />
                <Button 
                  type="button"
                  onClick={handleSirenValidation}
                  disabled={siren.length !== 9 || sirenLocked}
                >
                  {t('common.verify')}
                </Button>
              </div>
              {sirenLocked && (
                <p className="text-sm text-muted-foreground">
                  {t('profile.sirenLocked')}
                </p>
              )}
              
              {companyInfo && (
                <div className="mt-4 p-4 bg-muted rounded-lg space-y-2">
                  <h3 className="font-semibold text-lg">{companyInfo.name}</h3>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                    <p><strong>{t('common.sirenValidation.companyDetails.siren')}:</strong> {companyInfo.siren}</p>
                    {companyInfo.status && (
                      <p><strong>{t('common.sirenValidation.companyDetails.status')}:</strong> {getStatusText(companyInfo.status, t)}</p>
                    )}
                    {companyInfo.creation_date && (
                      <p><strong>{t('common.sirenValidation.companyDetails.creationDate')}:</strong> {new Date(companyInfo.creation_date).toLocaleDateString()}</p>
                    )}
                    {companyInfo.company_category && (
                      <p><strong>{t('common.sirenValidation.companyDetails.category')}:</strong> {companyInfo.company_category}</p>
                    )}
                    {companyInfo.activity && (
                      <p className="col-span-2"><strong>{t('common.sirenValidation.companyDetails.mainActivity')}:</strong> {companyInfo.activity}</p>
                    )}
                    {companyInfo.address && (
                      <p className="col-span-2"><strong>{t('common.sirenValidation.companyDetails.address')}:</strong> {companyInfo.address}</p>
                    )}
                    {companyInfo.staff_category && (
                      <p className="col-span-2">
                        <strong>{t('common.sirenValidation.companyDetails.staffing')}:</strong> {getStaffCategory(companyInfo.staff_category)}
                        {companyInfo.staff_year && ` (${companyInfo.staff_year})`}
                      </p>
                    )}
                  </div>
                </div>
              )}
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