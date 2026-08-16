/**
 * app/RequireAuth.tsx
 *
 * JA: 認証ガード。未ログインならログイン画面へ飛ばす。useMe() が 401 を返す＝未ログイン。
 *     保護したいルートをこれで包む（router.tsx で使用）。判定中はローディングを出す。
 * VI: Chốt chặn xác thực. Chưa đăng nhập thì đẩy về trang login. useMe() trả 401 = chưa đăng nhập.
 *     Bọc các route cần bảo vệ bằng component này (dùng trong router.tsx). Đang xét thì hiển thị loading.
 */
import { Navigate } from 'react-router-dom'

import { useMe } from '@/features/auth/api/hooks'
import { useI18n } from '@/shared/i18n'
import { LoadingText, PageContainer } from '@/shared/ui'

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const me = useMe()
  const { t } = useI18n()

  if (me.isPending)
    return (
      <PageContainer width="narrow">
        <LoadingText>{t('auth.checking')}</LoadingText>
      </PageContainer>
    )
  // JA: 取得失敗（401/403）＝未ログイン → ログイン画面へ。
  // VI: Lấy thất bại (401/403) = chưa đăng nhập -> tới trang login.
  if (me.isError) return <Navigate to="/login" replace />

  return <>{children}</>
}
