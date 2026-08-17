/**
 * features/auth/components/SignupForm.tsx
 *
 * JA: 新規登録フォーム。LoginFormと同じ構造(UIとフックの結線のみ)。
 *     ★発表デモでの同時利用向け。demo/demo12345の単一共有アカウントだと参加者全員の
 *     データが混ざってしまうため、聴衆が各自ここで自分のアカウントを作れるようにする。
 * VI: Form đăng ký mới. Cấu trúc giống LoginForm (chỉ nối UI với hook).
 *     ★Dùng cho việc nhiều người dùng đồng thời khi demo thuyết trình. Tài khoản
 *     demo/demo12345 dùng chung sẽ làm dữ liệu mọi người trộn lẫn, nên cho khán giả
 *     tự tạo tài khoản riêng ở đây.
 */
import { useState } from 'react'

import { useI18n } from '@/shared/i18n'
import { Button, ErrorText, Input } from '@/shared/ui'

import { useSignup } from '../api/hooks'

export function SignupForm({ onSuccess }: { onSuccess: () => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const signup = useSignup()
  const { t } = useI18n()

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    signup.mutate({ username, password }, { onSuccess })
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3">
      <Input
        placeholder={t('auth.signup.username')}
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        autoComplete="username"
      />
      <Input
        type="password"
        placeholder={t('auth.signup.password')}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        autoComplete="new-password"
      />
      <Button type="submit" variant="primary" block disabled={signup.isPending}>
        {signup.isPending ? t('auth.signup.submitting') : t('auth.signup.submit')}
      </Button>
      {signup.isError && <ErrorText>{(signup.error as Error).message}</ErrorText>}
    </form>
  )
}
