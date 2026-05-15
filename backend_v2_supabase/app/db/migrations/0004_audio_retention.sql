-- 20일 지난 오디오 자동 정리
-- 1) Storage 객체 삭제 (storage.objects DELETE → 실제 파일 cleanup)
-- 2) frequencies.audio_path NULL 처리 (대본 row 자체는 영구 보존)
--
-- 8 카테고리 × 2 slot × 20일 × 평균 12MB ≈ 3.8GB 누적 상한
-- Free 1GB 초과 → Pro 플랜 필요 (월 $25, 100GB 포함)

create extension if not exists pg_cron;
grant usage on schema cron to postgres;

create or replace function public.cleanup_old_audio()
returns table (deleted_count int, freed_bytes bigint)
language plpgsql
security definer
set search_path = public, storage
as $$
declare
    v_deleted int := 0;
    v_freed   bigint := 0;
    v_cutoff  timestamptz := now() - interval '20 days';
    rec       record;
    obj_size  bigint;
begin
    for rec in
        select id, audio_path
        from public.frequencies
        where audio_path is not null
          and created_at < v_cutoff
    loop
        select coalesce(sum((metadata->>'size')::bigint), 0)
        into   obj_size
        from   storage.objects
        where  bucket_id = 'briefly-audio'
          and  name = rec.audio_path;

        delete from storage.objects
         where bucket_id = 'briefly-audio'
           and name = rec.audio_path;

        update public.frequencies
           set audio_path = null
         where id = rec.id;

        v_deleted := v_deleted + 1;
        v_freed   := v_freed + obj_size;
    end loop;

    deleted_count := v_deleted;
    freed_bytes   := v_freed;
    return next;
end;
$$;

-- 매일 18:00 UTC = 03:00 KST 실행 (한가한 시간)
select cron.schedule(
    'cleanup-old-audio-daily',
    '0 18 * * *',
    $$select public.cleanup_old_audio();$$
);
