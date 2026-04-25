import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://hdpbzflntprxnctucyfp.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkcGJ6ZmxudHByeG5jdHVjeWZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzOTI4NzksImV4cCI6MjA4OTk2ODg3OX0.Uw942S1TgTwJANz6p-3VReJuB8F-0cVDOTt8SpWq02s'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)