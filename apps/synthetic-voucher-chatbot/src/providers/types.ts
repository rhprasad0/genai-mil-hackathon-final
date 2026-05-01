import { z } from 'zod'
import type { ChatMessage, Determination, ProviderId, SyntheticVoucher } from '../domain/types'

export type ProviderInput = {
  systemPrompt: string
  messages: ChatMessage[]
  voucherState: SyntheticVoucher
  allowedDeterminations: Determination[]
}

export const providerOutputSchema = z.object({
  assistantMessage: z.string(),
  extractedFields: z
    .object({
      travelerPersona: z.string().optional(),
      tripPurpose: z.string().optional(),
      dateRange: z.string().optional(),
      category: z.enum(['lodging', 'meal', 'transit', 'misc']).optional(),
      amountSyntheticCredits: z.number().int().nonnegative().max(100000).optional(),
      fakeReceiptPresent: z.boolean().optional(),
      amountMatchesAuthorization: z.boolean().optional(),
      explanation: z.string().max(500).optional(),
    })
    .partial()
    .optional(),
  requestedField: z
    .enum([
      'travelerPersona',
      'tripPurpose',
      'dateRange',
      'category',
      'amountSyntheticCredits',
      'fakeReceiptPresent',
      'amountMatchesAuthorization',
      'explanation',
    ])
    .optional(),
  safetyBoundaryOk: z.boolean(),
  providerStatus: z.enum(['ok', 'unavailable']).optional(),
})

export type ProviderOutput = z.infer<typeof providerOutputSchema>

export type ChatProvider = {
  id: ProviderId | string
  label: string
  complete(input: ProviderInput): Promise<ProviderOutput>
}
