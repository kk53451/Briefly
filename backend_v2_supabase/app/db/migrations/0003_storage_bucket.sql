-- Briefly v3 storage bucket: briefly-audio (public)
-- Stores podcast MP3s under {date}/{category}_{slot}.mp3
-- Public bucket → 모바일은 getPublicUrl()로 영구 URL 생성

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
    'briefly-audio',
    'briefly-audio',
    true,
    50 * 1024 * 1024,                 -- 50MB 상한 (오디오 1개 평균 10MB)
    array['audio/mpeg', 'audio/mp3']
)
on conflict (id) do update
set
    public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

-- Public bucket이라 anon read는 자동 허용. write는 service_role 만.
-- 추후 private 전환 시 storage.objects RLS 정책 추가 필요.
