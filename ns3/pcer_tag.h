#ifndef PCER_TAG_H
#define PCER_TAG_H

#include "ns3/tag.h"
#include "ns3/packet.h"
#include "ns3/uinteger.h"

namespace ns3 {

/**
 * @brief Tag to carry Priority-Coupled Elastic Routing (PCER) urgency level.
 * 
 * Tags:
 * 0: Critical (Low Latency)
 * 1: Standard (Balanced)
 * 2: Bulk (Energy Efficient)
 */
class PcErTag : public Tag
{
public:
  static TypeId GetTypeId (void);
  virtual TypeId GetInstanceTypeId (void) const;
  virtual uint32_t GetSerializedSize (void) const;
  virtual void Serialize (TagBuffer i) const;
  virtual void Deserialize (TagBuffer i);
  virtual void Print (std::ostream &os) const;

  PcErTag ();
  PcErTag (uint8_t urgency);
  
  void Set (uint8_t urgency);
  uint8_t Get (void) const;

private:
  uint8_t m_urgency;
};

} // namespace ns3

#endif /* PCER_TAG_H */
