'use client'

export const dynamic = 'force-dynamic'

import { useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useToast } from '@/components/ui/use-toast'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { signInWithEmail, signUpWithEmail, signInWithGoogle, requestPasswordReset, resetPassword } from './api/auth'
import { useAuth } from '@/components/AuthContext'
import { FcGoogle } from 'react-icons/fc'
import { AuthError } from '@supabase/supabase-js'
import HCaptcha from '@hcaptcha/react-hcaptcha'
import { useTranslation } from '@/hooks/useTranslation'

console.log('Environment variables:', {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.slice(0, 10) + '...',
})

// Définir les props du SignUpForm
interface SignUpFormProps {
  username: string;
  setUsername: (value: string) => void;
  siretNumber: string;
  setSiretNumber: (value: string) => void;
  phone: string;
  setPhone: (value: string) => void;
  address: string;
  setAddress: (value: string) => void;
  captcha: any;
  setCaptchaToken: (token: string) => void;
}

const SignUpForm = ({
  username,
  setUsername,
  siretNumber,
  setSiretNumber,
  phone,
  setPhone,
  address,
  setAddress,
  captcha,
  setCaptchaToken
}: SignUpFormProps) => {
  const { t } = useTranslation()
  
  return (
    <div className="space-y-4">
      <Input
        placeholder={t('common.username')}
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
      />
      <Input
        placeholder={t('common.siretNumber')}
        value={siretNumber}
        onChange={(e) => setSiretNumber(e.target.value)}
        required
      />
      <Input
        placeholder={t('common.phone')}
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        required
      />
      <Input
        placeholder={t('common.address')}
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        required
      />
      <div className="mt-4">
        <HCaptcha
          ref={captcha}
          sitekey="4724bc9e-e97e-4b72-a166-4d1680f09926"
          onVerify={(token) => setCaptchaToken(token)}
          onExpire={() => setCaptchaToken('')}
        />
      </div>
    </div>
  )
}

const ResetPasswordCard = ({ setIsLogin }: { setIsLogin: (value: boolean) => void }) => {
  const [email, setEmail] = useState('')
  const { toast } = useToast()
  const { t } = useTranslation()

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await requestPasswordReset(email)
      toast({
        title: t('common.success'),
        description: t('auth.verifyEmail'),
      })
      setIsLogin(true)
    } catch (error) {
      toast({
        title: t('common.error'),
        description: t('auth.updateError'),
        variant: 'destructive',
      })
    }
  }

  return (
    <Card className="w-[400px] shadow-lg border bg-card">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl text-center text-foreground">
          {t('auth.resetPassword')}
        </CardTitle>
        <p className="text-sm text-muted-foreground text-center">
          {t('auth.verifyEmail')}
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleResetPassword} className="space-y-4">
          <Input
            type="email"
            placeholder={t('common.email')}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <div className="flex flex-col space-y-2">
            <Button type="submit" className="w-full">
              {t('common.sendLink')}
            </Button>
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => setIsLogin(true)}
              className="w-full"
            >
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

export default function Home() {
  const [isLogin, setIsLogin] = useState(true)
  const [isResetPassword, setIsResetPassword] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const [siretNumber, setSiretNumber] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const { toast } = useToast()
  const router = useRouter()
  const { setIsAuthenticated } = useAuth()
  const captcha = useRef(null)
  const [captchaToken, setCaptchaToken] = useState('')
  const { t } = useTranslation()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (isLogin) {
        console.log(t('auth.attemptingLogin'), { email })
        const { session, user } = await signInWithEmail(email, password)
        if (session) {
          setIsAuthenticated(true)
          router.push('/dashboard')
        } else {
          toast({
            title: t('common.error'),
            description: t('auth.invalidCredentials'),
            variant: 'destructive',
          })
        }
      } else {
        if (!captchaToken) {
          toast({
            title: t('common.error'),
            description: t('auth.completeCaptcha'),
            variant: 'destructive',
          })
          return
        }

        console.log(t('auth.attemptingSignup'))
        const { user } = await signUpWithEmail(email, password, {
          username,
          siret_number: siretNumber,
          phone,
          address
        }, captchaToken)
        
        if (user) {
          if (captcha.current) {
            // @ts-ignore
            captcha.current.resetCaptcha()
          }
          setCaptchaToken('')
          toast({
            title: t('common.success'),
            description: t('auth.verifyEmail'),
          })
          setIsLogin(true)
        }
      }
    } catch (error) {
      console.error('Détails de l\'erreur d\'authentification:', error)
      const message = error instanceof AuthError ? error.message : t('auth.authenticationFailed')
      toast({
        title: t('common.error'),
        description: message,
        variant: 'destructive',
      })
    }
  }

  const handleModeChange = () => {
    setIsLogin(!isLogin)
    setCaptchaToken('')
    setEmail('')
    setPassword('')
    if (!isLogin) {
      // Réinitialiser les champs du formulaire d'inscription
      setUsername('')
      setSiretNumber('')
      setPhone('')
      setAddress('')
    }
    if (captcha.current) {
      // @ts-ignore
      captcha.current.resetCaptcha()
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      {isResetPassword ? (
        <ResetPasswordCard setIsLogin={(value) => {
          setIsLogin(value)
          setIsResetPassword(false)
        }} />
      ) : (
        <Card className="w-[400px] shadow-lg border bg-card">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center text-foreground">
              {isLogin ? t('common.signIn') : t('common.signUp')}
            </CardTitle>
            <p className="text-sm text-muted-foreground text-center">
              {isLogin ? t('common.securityMessage') : t('common.createAccount')}
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              {!isLogin && (
                <SignUpForm
                  username={username}
                  setUsername={setUsername}
                  siretNumber={siretNumber}
                  setSiretNumber={setSiretNumber}
                  phone={phone}
                  setPhone={setPhone}
                  address={address}
                  setAddress={setAddress}
                  captcha={captcha}
                  setCaptchaToken={setCaptchaToken}
                />
              )}
              <Input
                type="email"
                placeholder={t('common.email')}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <Input
                type="password"
                placeholder={t('common.password')}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <Button 
                type="submit" 
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
              >
                {isLogin ? t('common.signIn') : t('common.signUp')}
              </Button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">{t('common.or')}</span>
              </div>
            </div>

            <Button
              variant="outline"
              onClick={() => signInWithGoogle()}
              className="w-full border-input bg-background hover:bg-accent hover:text-accent-foreground"
            >
              <FcGoogle className="mr-2 h-5 w-5" />
              {t('common.signInWithGoogle')}
            </Button>

            <Button
              variant="ghost"
              onClick={handleModeChange}
              className="w-full hover:bg-accent hover:text-accent-foreground"
            >
              {isLogin ? t('auth.dontHaveAccount') : t('auth.alreadyHaveAccount')}
            </Button>

            {isLogin && (
              <Button
                type="button"
                variant="link"
                className="px-0 font-normal"
                onClick={() => setIsResetPassword(true)}
              >
                {t('auth.forgotPassword')}
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}