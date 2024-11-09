import { Button } from "@/components/ui/button"
import { useTranslation } from "@/hooks/useTranslation"

export default function LanguageSelector() {
  const { language, changeLanguage } = useTranslation()

  const toggleLanguage = () => {
    const newLang = language === 'en' ? 'fr' : 'en'
    changeLanguage(newLang)
  }

  return (
    <Button 
      variant="ghost" 
      onClick={toggleLanguage}
      className="w-9 px-0"
    >
      {language === 'en' ? '🇬🇧' : '🇫🇷'}
    </Button>
  )
} 