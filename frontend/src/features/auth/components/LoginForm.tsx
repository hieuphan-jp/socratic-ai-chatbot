/**
 * features/auth/components/LoginForm.tsx
 *
 * JA: ログインフォーム。UIとフックの結線のみを担い、通信ロジックは api フックに任せる。
 *     成功時の遷移は呼び出し側(page)に委ねる（onSuccess を受け取る）＝部品は再利用しやすく保つ。
 *     ★文言は t() 経由。ここに日本語を直接書かないこと(3言語に出し分けられなくなるため)。
 * VI: Form đăng nhập. Chỉ nối UI với hook; logic giao tiếp giao cho api hook.
 *     Điều hướng khi thành công do bên gọi (page) quyết định (nhận onSuccess) = giữ component dễ tái dùng.
 *     ★Câu chữ đi qua t(). KHÔNG viết thẳng tiếng Nhật ở đây (sẽ không tách được 3 ngôn ngữ).
 */
import { useState } from 'react'

import { useI18n } from '@/shared/i18n'
import { Button, ErrorText, Input } from '@/shared/ui'

import { useLogin } from '../api/hooks'

export function LoginForm({ onSuccess }: { onSuccess: () => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const login = useLogin()
  const { t } = useI18n()

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    login.mutate({ username, password }, { onSuccess })
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3">
      <Input
        placeholder={t('auth.login.username')}
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        autoComplete="username"
      />
      <Input
        type="password"
        placeholder={t('auth.login.password')}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        autoComplete="current-password"
      />
      <Button type="submit" variant="primary" block disabled={login.isPending}>
        {login.isPending ? t('auth.login.submitting') : t('auth.login.submit')}
      </Button>
      {login.isError && <ErrorText>{(login.error as Error).message}</ErrorText>}
    </form>
  )
}
