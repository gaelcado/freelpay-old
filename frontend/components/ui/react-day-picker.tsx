'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { Calendar as CalendarIcon } from 'lucide-react'
import { DateRange } from 'react-day-picker'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'

export function DateRangePicker({
  className,
  onChange,
}: {
  className?: string
  onChange: (date: DateRange | undefined) => void
}) {
  const [date, setDate] = useState<DateRange | undefined>()

  return (
    <div className={cn('grid gap-2', className)}>
      <Popover>
        <PopoverTrigger asChild>
          <Button
            id="date"
            variant={'outline'}
            className={cn(
              'w-[400px] justify-start text-left font-normal', // Augmenter la largeur ici
              !date && 'text-muted-foreground'
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {date?.from ? (
              date.to ? (
                <>
                  {format(date.from, 'LLL dd, y')} -{' '}
                  {format(date.to, 'LLL dd, y')}
                </>
              ) : (
                format(date.from, 'LLL dd, y')
              )
            ) : (
              <span>Pick a date</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start" style={{ zIndex: 1000 }}>
          <Calendar
            mode="range"
            defaultMonth={date?.from}
            selected={date}
            onSelect={(newDate: DateRange | undefined) => {
              setDate(newDate)
              onChange(newDate)
            }}
            numberOfMonths={1}
          />
        </PopoverContent>
      </Popover>
    </div>
  )
}