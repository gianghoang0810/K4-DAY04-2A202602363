# Hướng dẫn nộp bài Lab Day 04 trên VLearn

## Xác định repository chung của nhóm

Mục tiêu của phần này là để cả nhóm làm việc trên đúng một repository và có
một link duy nhất dùng cho việc nộp bài. Repository nguồn của Lab là
[K4-Day04-Prompt-Engineering-Tool-Calling-Labs](https://github.com/VinUni-AI20k/K4-Day04-Prompt-Engineering-Tool-Calling-Labs).
Nhóm trưởng là người tạo fork; các thành viên không tạo những repository nộp
bài riêng biệt.

Repository nộp bài nên dùng tên theo mẫu sau. Thay `KX` bằng mã khóa của nhóm
và thay `TenNhom` bằng tên nhóm đã thống nhất:

```text
KX-DAY04-TenNhom/
├── TEAMMATES.md
└── ...các file của bài Lab...
```

1. Nhóm trưởng mở repository nguồn ở link phía trên và chọn **Fork** trên
   GitHub.
2. Trong fork, nhóm trưởng đặt tên repository theo mẫu
   `KX-DAY04-TenNhom` và giữ toàn bộ starter code của bài Lab.
3. Nhóm trưởng cấp quyền cộng tác trên fork cho các thành viên hoặc thiết lập
   quy trình pull request để đóng góp của họ được đưa vào cùng repository.
4. Nhóm trưởng tạo `TEAMMATES.md` tại thư mục gốc, ghi họ tên đầy đủ, MSSV,
   GitHub username và vai trò của từng người.

Quy mô nhóm không được quy định trong hướng dẫn nguồn; `TEAMMATES.md` phải phản
ánh đúng nhóm thực tế. Phần này hoàn thành khi nhóm trưởng gửi một link fork mà
mọi thành viên đều mở được, và khi thư mục gốc của fork đã có
`TEAMMATES.md`.

## Đưa đóng góp của từng thành viên vào repository

Mục tiêu của phần này là tạo bằng chứng đóng góp ngay trong Git history. Chỉ có
tên trong `TEAMMATES.md` chưa đủ: mỗi thành viên phải có ít nhất một commit của
chính mình xuất hiện trên branch cuối cùng được dùng để nộp. Một commit chỉ nằm
trên máy cá nhân hoặc trên branch chưa được merge sẽ chưa đáp ứng điều kiện
này.

Trước khi tạo commit, mỗi thành viên nên kiểm tra Git identity trong bản clone
của mình. Email có thể là email gắn với GitHub hoặc địa chỉ `noreply` do GitHub
cung cấp; không cần công khai email cá nhân nếu người học không muốn.

```powershell
git config user.name
git config user.email
```

1. Mỗi thành viên clone đúng fork chung của nhóm và tạo một branch cho phần
   việc của mình.

   ```powershell
   git clone <LINK_REPOSITORY_CHUNG>
   cd KX-DAY04-TenNhom
   git switch -c contrib/<GITHUB_USERNAME>
   ```

2. Thành viên hoàn thành phần việc được phân công, kiểm tra các file thay đổi
   bằng `git status`, rồi tạo ít nhất một commit dưới Git identity của mình.

   ```powershell
   git status
   git add <CAC_FILE_DA_THAY_DOI>
   git commit -m "feat(scope): describe contribution"
   ```

3. Thành viên push branch lên fork chung và tạo pull request vào branch mà
   nhóm sẽ nộp.

   ```powershell
   git push -u origin contrib/<GITHUB_USERNAME>
   ```

4. Nhóm trưởng review và merge đóng góp. Không dùng squash merge nếu thao tác
   đó làm mất commit riêng cần dùng để chứng minh đóng góp của thành viên.

Sau khi merge, chạy lệnh sau trên branch nộp bài. Kết quả cần có ít nhất một
commit tương ứng với từng thành viên trong `TEAMMATES.md`:

```powershell
git log --format="%h | %an <%ae> | %s"
```

Nếu thiếu một người, kiểm tra branch của thành viên đã được push và merge chưa,
hoặc commit có đang dùng nhầm Git identity hay không. Chỉ chuyển sang bước nộp
bài khi lịch sử của repository chung đã thể hiện đầy đủ các thành viên.

## Kiểm tra repository trước khi nộp

Mục tiêu của phần này là bảo đảm link chung chứa đúng artifact của Lab và không
kèm dữ liệu không nên công khai. Nhóm trưởng thực hiện kiểm tra trên branch cuối
cùng, nhưng các thành viên cũng nên mở link GitHub để tự đối chiếu trước khi
nộp trên VLearn.

1. Đối chiếu các deliverable của Lab: `system_prompt.md`, `tools.yaml`,
   `version_log.csv`, run evidence, team eval, adversarial evidence,
   transcript, UI và report.
2. Mở `TEAMMATES.md` trên GitHub và kiểm tra đủ họ tên, MSSV, GitHub username
   và vai trò của mọi thành viên.
3. Mở lịch sử commit của branch nộp bài và xác nhận mỗi thành viên có ít nhất
   một commit xuất hiện trong lịch sử đó.
4. Kiểm tra repository không chứa `.env`, API key, token, `.venv`, cache,
   generated ticket hoặc dữ liệu thật.
5. Sao chép URL tại trang gốc của fork chung; không dùng URL của repository
   nguồn, branch cá nhân, commit riêng hoặc pull request.

:::checklist{title="Repository sẵn sàng để nộp" tone="success"}
- [X] Fork chung mở được bằng link dự định nộp.
- [X] `TEAMMATES.md` có đủ thành viên và MSSV.
- [X] Mỗi thành viên có ít nhất một commit đã được merge.
- [X] Các deliverable của Lab nằm trên branch nộp bài.
- [X] Repository không chứa secret hoặc dữ liệu thật.
:::

Checkpoint của phần này là một URL repository duy nhất đã được cả nhóm kiểm
tra. Giữ nguyên URL đó để tất cả thành viên dùng ở bước tiếp theo.

## Nộp cùng một link trên VLearn

Mục tiêu cuối cùng là để VLearn ghi nhận bài nộp của từng người, trong khi
evidence kỹ thuật vẫn nằm ở một repository chung. Vì vậy, không chỉ nhóm trưởng
mà mọi thành viên có tên trong `TEAMMATES.md` đều phải thực hiện thao tác nộp
bài trên tài khoản VLearn của chính mình.

1. Nhóm trưởng đăng nhập VLearn, mở bài Lab Day 04 và nộp URL của fork chung.
2. Từng thành viên đăng nhập tài khoản VLearn của mình, mở cùng bài Lab và nộp
   chính xác URL mà nhóm trưởng đã dùng.
3. Sau khi nộp, mỗi người mở lại bài nộp để xác nhận URL đã được lưu đầy đủ và
   trỏ đến đúng repository chung.
4. Cả nhóm đối chiếu lần cuối: số bài nộp trên VLearn phải tương ứng với số
   người trong `TEAMMATES.md`, và tất cả các bài nộp phải chứa cùng một URL.

Không nộp link repository cá nhân khác, link repository nguồn, link pull
request hoặc link tới một commit đơn lẻ. Bài nộp hoàn thành khi nhóm trưởng và
toàn bộ thành viên đều thấy link fork chung trong phần bài nộp của chính mình
trên VLearn.
