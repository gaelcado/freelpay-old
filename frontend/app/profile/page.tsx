// app/profile/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useToast } from "@/components/ui/use-toast"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface OriginalData {
  email: string;
  siret_number: string;
  phone: string;
  address: string;
}

export default function Profile() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [siret, setSiret] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [isVerified, setIsVerified] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [originalData, setOriginalData] = useState<OriginalData>({
    email: '',
    siret_number: '',
    phone: '',
    address: ''
  });
  const { toast } = useToast()

  useEffect(() => {
    fetchUserProfile()
  }, [])

  const fetchUserProfile = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_URL}/users/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const userData = response.data
      setName(userData.username)
      setEmail(userData.email)
      setSiret(userData.siret_number)
      setPhone(userData.phone)
      setAddress(userData.address)
      setIsVerified(userData.is_verified)
      setOriginalData({
        email: userData.email,
        siret_number: userData.siret_number,
        phone: userData.phone,
        address: userData.address
      })
    } catch (error) {
      console.error('Error fetching user profile:', error)
    }
  }

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
      address !== originalDataTyped.address;
    setHasChanges(hasChanged);
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const token = localStorage.getItem('token')
      await axios.put(`${API_URL}/users/update`, {
        email,
        siret_number: siret,
        phone,
        address
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      toast({
        title: 'Profile Updated',
        description: 'Your profile has been successfully updated.',
      })
      setHasChanges(false)
      setOriginalData({ email, siret_number: siret, phone, address })
    } catch (error) {
      console.error('Error updating profile:', error)
      toast({
        title: 'Error',
        description: 'Failed to update profile. Please try again.',
        variant: 'destructive',
      })
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const formData = new FormData()
      formData.append('file', file)  // Changez 'id_document' en 'file'
      try {
        const token = localStorage.getItem('token')
        await axios.post(`${API_URL}/users/upload-id`, formData, {
          headers: { 
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${token}`
          }
        })
        toast({
          title: 'ID Document Uploaded',
          description: 'Your ID document has been successfully uploaded for verification.',
        })
      } catch (error) {
        console.error('Error uploading ID document:', error)
        toast({
          title: 'Error',
          description: 'Failed to upload ID document. Please try again.',
          variant: 'destructive',
        })
      }
    }
  }

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-3xl font-bold">My Profile</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
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
              <Label htmlFor="siret">SIRET Number</Label>
              <Input
                id="siret"
                value={siret}
                onChange={(e) => handleInputChange(setSiret, e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                type="tel"
                value={phone}
                onChange={(e) => handleInputChange(setPhone, e.target.value)}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="address">Address</Label>
            <Input
              id="address"
              value={address}
              onChange={(e) => handleInputChange(setAddress, e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="id-document">ID Document</Label>
            <Input
              id="id-document"
              type="file"
              onChange={handleFileUpload}
            />
          </div>
          <div className="flex items-center space-x-2">
            <span>Verification Status:</span>
            <Badge variant={isVerified ? "default" : "secondary"}>
              {isVerified ? 'Verified' : 'Not Verified'}
            </Badge>
          </div>
          <Button type="submit" className="w-full" disabled={!hasChanges}>
            Update Profile
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}