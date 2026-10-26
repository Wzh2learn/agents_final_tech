"""Reproduce inactive-parent audit on a tiny CPU model; no Qwen or generation."""
import torch,torch.nn as nn,hashlib,json,importlib.metadata as meta
from peft import LoraConfig,get_peft_model
torch.set_num_threads(1)
class Tiny(nn.Module):
    def __init__(self):
        super().__init__()
        self.proj=nn.Linear(2,2,bias=False,device="cpu")
        with torch.no_grad(): self.proj.weight.zero_()
    def forward(self,x): return self.proj(x)
m=get_peft_model(Tiny(),LoraConfig(r=1,lora_alpha=1,target_modules=["proj"]),adapter_name="ordinary_parent")
for layer in m.modules():
    if hasattr(layer,"lora_A") and "ordinary_parent" in layer.lora_A:
        with torch.no_grad():
            layer.lora_A["ordinary_parent"].weight.fill_(1)
            layer.lora_B["ordinary_parent"].weight.fill_(1)
x=torch.ones(1,2,device="cpu")
m.eval()
with torch.no_grad(): parent=m(x).tolist()
def digest():
    h=hashlib.sha256()
    for n,p in m.named_parameters():
        if ".ordinary_parent." in n:h.update(p.detach().cpu().numpy().tobytes())
    return h.hexdigest()
before=digest()
m.add_adapter("b2_child",LoraConfig(r=1,lora_alpha=1,target_modules=["proj"]))
m.set_adapter("b2_child")
m.eval()
with torch.no_grad():
    child=m(x).tolist()
    with m.disable_adapter():base=m(x).tolist()
record={"phase":"audit_synthetic_cpu_counterexample","peft":meta.version("peft"),"device":str(next(m.parameters()).device),"active_adapter":m.active_adapter,"parent_output":parent,"child_output":child,"base_output":base,"parent_hash_unchanged":before==digest(),"child_equals_base":child==base,"child_equals_parent":child==parent,"scientific_generation_attempts":0,"training_runs":0,"endpoint_calls":0}
assert record["parent_hash_unchanged"] and record["child_equals_base"] and not record["child_equals_parent"]
print(json.dumps(record))

