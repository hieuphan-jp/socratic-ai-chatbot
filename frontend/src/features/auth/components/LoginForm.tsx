/**
 * features/auth/components/LoginForm.tsx
 *
 * JA: ログインフォーム。UIとフックの結線のみを担い、通信ロジックは api フックに任せる。
 *     成功時の遷移は呼び出し側(page)に委ねる（onSuccess を受け取る）＝部品は再利用しやすく保つ。
 * VI: Form đăng nhập. Chỉ nối UI với hook; logic giao tiếp giao cho api hook.
 *     Điều hướng khi thành công do bên gọi (page) quyết định (nhận onSuccess) = giữ component dễ tái dùng.
 */
import { useState } from 'react'

import { Button, ErrorText, Input } from '@/shared/ui'

import { useLogin } from '../api/hooks'

export function LoginForm({ onSuccess }: { onSuccess: () => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const login = useLogin()

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    login.mutate({ username, password }, { onSuccess })
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 10, maxWidth: 280 }}>
      <Input
        placeholder="ユーザー名 / Tên đăng nhập"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        autoComplete="username"
      />
      <Input
        type="password"
        placeholder="パスワード / Mật khẩu"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        autoComplete="current-password"
      />
      <Button type="submit" disabled={login.isPending}>
        {login.isPending ? 'ログイン中… / Đang đăng nhập…' : 'ログイン / Đăng nhập'}
      </Button>
      {login.isError && <ErrorText>{(login.error as Error).message}</ErrorText>}
    </form>
  )
}
