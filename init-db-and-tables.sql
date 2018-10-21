-- Create the database
CREATE DATABASE "RoboragiDB"
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Create the requests table
CREATE SEQUENCE public.requests_id_seq;

CREATE TABLE public.requests
(
    id integer NOT NULL DEFAULT nextval('public.requests_id_seq'::regclass),
    name character varying(320) COLLATE pg_catalog."default",
    type character varying(16) COLLATE pg_catalog."default",
    requester character varying(50) COLLATE pg_catalog."default",
    subreddit character varying(50) COLLATE pg_catalog."default",
    requesttimestamp timestamp without time zone DEFAULT now(),
    CONSTRAINT requests_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

-- Create the comments table
CREATE TABLE public.comments
(
    commentid character varying(16) COLLATE pg_catalog."default" NOT NULL,
    requester character varying(50) COLLATE pg_catalog."default",
    subreddit character varying(50) COLLATE pg_catalog."default",
    hadrequest boolean DEFAULT false,
    CONSTRAINT comments_pkey PRIMARY KEY (commentid)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

CREATE INDEX commentid_idx
    ON public.comments USING btree
    (commentid COLLATE pg_catalog."default" varchar_ops)
    TABLESPACE pg_default;