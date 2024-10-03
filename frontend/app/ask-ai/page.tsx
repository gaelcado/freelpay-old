'use client'

import { RouteGuard } from '@/components/RouteGuard'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useToast } from '@/components/ui/use-toast'
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Loader2, Send, AlertCircle, Bot } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function AskAI() {
  return (
    <RouteGuard>
      <AskAIContent />
    </RouteGuard>
  )
}

function AskAIContent() {
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setResponse('')
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        router.push('/')
        return
      }
      const response = await axios.post(`${API_URL}/ai/query`, { query }, {
        headers: { Authorization: `Bearer ${token}` },
      })
      setResponse(response.data.answer)
    } catch (error) {
      console.error('Error processing query:', error)
      setError('Failed to process query. Please try again.')
      toast({
        title: 'Error',
        description: 'Failed to process query. Please try again.',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="text-2xl sm:text-3xl font-bold flex items-center justify-center sm:justify-start">
            <Bot className="mr-2 h-6 w-6 sm:h-8 sm:w-8" />
            Ask AI
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <Input
                placeholder="Ask a question about your network..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pr-20"
              />
              <Button 
                type="submit" 
                disabled={isLoading || query.trim() === ''} 
                className="absolute right-0 top-0 bottom-0"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
                <span className="sr-only">
                  {isLoading ? 'Processing...' : 'Ask AI'}
                </span>
              </Button>
            </div>
          </form>
          {response && (
            <div className="mt-6 bg-secondary p-4 rounded-md">
              <h2 className="text-lg sm:text-xl font-semibold mb-2 flex items-center">
                <Bot className="mr-2 h-5 w-5" />
                AI Response:
              </h2>
              <p className="text-secondary-foreground text-sm sm:text-base">{response}</p>
            </div>
          )}
        </CardContent>
        <CardFooter className="text-xs sm:text-sm text-muted-foreground">
          Tip: Ask specific questions about your network for the best results.
        </CardFooter>
      </Card>
    </div>
  )
}