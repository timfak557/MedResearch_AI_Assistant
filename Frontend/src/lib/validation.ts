import { z } from "zod";

export const MAX_QUERY_LENGTH = 2000;

export const chatMessageSchema = z
  .string()
  .trim()
  .min(1, "Please enter a valid research question.")
  .max(MAX_QUERY_LENGTH, `Questions are limited to ${MAX_QUERY_LENGTH} characters.`);

export const searchFormSchema = z.object({
  query: z
    .string()
    .trim()
    .min(1, "Please enter a search query.")
    .max(MAX_QUERY_LENGTH, `Queries are limited to ${MAX_QUERY_LENGTH} characters.`),
  top_k: z.coerce.number().int().min(1).max(20).default(10),
  source: z.string().optional(),
  question_type: z.string().optional(),
  focus: z.string().optional(),
});

export type SearchFormValues = z.infer<typeof searchFormSchema>;
