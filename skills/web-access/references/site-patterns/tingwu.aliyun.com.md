# tingwu.aliyun.com

Discovered: 2026-06-02

## Verified Flow

- Use CDP with the user's logged-in Chrome session.
- For folder pages such as `https://tingwu.aliyun.com/folders/315194`, click `新建` and choose `上传本地音视频文件`.
- The upload modal accepts local `.m4a` files through `input[type=file]`.
- The page displays these limits: one audio file up to 500M, one upload batch up to 50 files.
- After clicking `开始转写`, completed records appear in the folder list and open to `/doc/transcripts/...`.

## Transcript Extraction

- On a completed transcript page, original transcript paragraphs were available in `.tingwu2_paragraphOrigin`.
- For short recipe audios, the DOM contained the complete transcript without using the export button.

## Notes

- Work in a self-created background tab and close it after extraction.
- Avoid touching an existing user-opened Tingwu tab unless explicitly asked.
