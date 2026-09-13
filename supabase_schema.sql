-- ============================================================
-- AraFakeNews evaluation study — Supabase schema
-- Run this once in your Supabase project's SQL Editor
-- (Project → SQL Editor → New query → paste → Run)
-- ============================================================

-- ------------------------------------------------------------
-- 1. Participants (demographics, one row per evaluator)
-- ------------------------------------------------------------
create table if not exists participants (
    user_id                   text primary key,
    created_at                timestamptz default now(),
    age_group                 text,
    gender                    text,
    education_stage           text,
    field_of_study            text,
    social_media_usage        text,
    media_trust                text,
    news_verification_habit   text
);

-- ------------------------------------------------------------
-- 2. Evaluations (one row per rating a user gives an image)
-- ------------------------------------------------------------
create table if not exists evaluations (
    evaluation_id   bigint generated always as identity primary key,
    user_id         text not null references participants(user_id),
    image_id        text not null,
    image_rating    int  not null check (image_rating between 1 and 5),
    title_rating    int  not null check (title_rating between 1 and 5),
    created_at      timestamptz default now(),

    -- a user can only rate a given image once
    unique (image_id, user_id)
);

create index if not exists idx_evaluations_image_id on evaluations (image_id);

-- ------------------------------------------------------------
-- 3. Convenience view: per-image average scores + count
--    (used for analysis / export, not required by the app itself)
-- ------------------------------------------------------------
create or replace view image_scores as
select
    image_id,
    count(*)                         as eval_count,
    round(avg(image_rating)::numeric, 2) as final_score_image,
    round(avg(title_rating)::numeric, 2) as final_score_title
from evaluations
group by image_id;

-- ------------------------------------------------------------
-- 4. Row Level Security
--    This app uses the public "anon" key from Streamlit, so we
--    allow anonymous insert + select on both tables. This is
--    fine for a research collection tool with random user IDs,
--    but do NOT put any sensitive/identifying data in these
--    tables if you go this route.
-- ------------------------------------------------------------
alter table participants enable row level security;
alter table evaluations  enable row level security;

create policy "Allow anon insert on participants"
    on participants for insert
    to anon
    with check (true);

create policy "Allow anon select on participants"
    on participants for select
    to anon
    using (true);

create policy "Allow anon insert on evaluations"
    on evaluations for insert
    to anon
    with check (true);

create policy "Allow anon select on evaluations"
    on evaluations for select
    to anon
    using (true);
