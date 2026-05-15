-- 0005 rename 으로 인한 cleanup_old_audio() 함수 참조 보수.
-- 0004 에 만들어진 함수는 public.frequencies 를 가리키고 있어서 rename 직후부터
-- 호출 시 에러가 발생. 본 마이그레이션으로 public.podcasts 참조로 교체.
--
-- 원격 DB 에는 Supabase migration
-- `20260419030644_fix_cleanup_old_audio_for_podcasts_rename` 로 이미 적용되었음.

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
        from public.podcasts
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

        update public.podcasts
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
